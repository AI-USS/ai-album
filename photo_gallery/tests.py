from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import Mock, patch
from PIL import Image
from django.test import TestCase, SimpleTestCase, Client, override_settings
from django.utils import timezone
from .models import Photographic, ColorizationJob
from .services.colorization import colorize, ColorizationError
from .services.jobs import run_one
import requests


def jpeg(size=(8, 6)):
    stream = BytesIO()
    Image.new('RGB', size, 'gray').save(stream, 'JPEG')
    return stream.getvalue()


class ClientTests(SimpleTestCase):
    def response(self, data=None, mime='image/jpeg', status=200):
        response = Mock(status_code=status, headers={'Content-Type': mime})
        response.iter_content.return_value = [jpeg() if data is None else data]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    @patch('photo_gallery.services.colorization.requests.post')
    def test_validated_result(self, post):
        post.return_value = self.response()
        result, model = colorize(jpeg())
        self.assertEqual(result, jpeg())
        self.assertEqual(model, 'unknown')
        self.assertIn('image', post.call_args.kwargs['files'])

    @patch('photo_gallery.services.colorization.requests.post')
    def test_invalid_responses(self, post):
        for response, code in [
            (self.response(mime='text/html'), 'invalid_response'),
            (self.response(data=b'broken'), 'invalid_response'),
            (self.response(data=jpeg((2, 2))), 'invalid_response'),
            (self.response(status=503), 'service_unavailable'),
        ]:
            with self.subTest(code=code):
                post.return_value = response
                with self.assertRaisesMessage(ColorizationError, code):
                    colorize(jpeg())
        post.side_effect = requests.Timeout()
        with self.assertRaisesMessage(ColorizationError, 'timeout'):
            colorize(jpeg())

    @patch('photo_gallery.services.colorization.requests.post')
    def test_output_limit(self, post):
        post.return_value = self.response(data=b'x' * 1000)
        with override_settings(COLORIZATION_MAX_BYTES=800):
            with self.assertRaisesMessage(ColorizationError, 'output_too_large'):
                colorize(jpeg())


class JobTests(TestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=jpeg(), width=8, height=6, format='JPEG', description='test')
        self.start = f'/{self.photo.pk}/colorize'

    def test_start_idempotent_and_csrf(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.start).status_code, 403)
        self.assertEqual(self.client.get(self.start).status_code, 405)
        first = self.client.post(self.start)
        second = self.client.post(self.start)
        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()['job_id'], second.json()['job_id'])
        self.assertEqual(ColorizationJob.objects.count(), 1)
        self.assertEqual(self.client.post('/999999/colorize').status_code, 404)

    @patch('photo_gallery.services.jobs.colorize', return_value=(jpeg(), 'test-model'))
    def test_worker_success_and_reuse(self, call):
        self.client.post(self.start)
        self.assertTrue(run_one())
        self.photo.refresh_from_db()
        self.assertEqual(bytes(self.photo.awers), jpeg())
        self.assertEqual(bytes(self.photo.colorized), jpeg())
        self.assertEqual(self.photo.colorized_model, 'test-model')
        self.assertEqual(self.client.get(f'/{self.photo.pk}/colorization').json()['status'], 'succeeded')
        response = self.client.get(f'/{self.photo.pk}/colorized?download=1')
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(self.client.post(self.start).status_code, 200)
        self.assertEqual(ColorizationJob.objects.count(), 1)
        self.assertFalse(run_one())

    @patch('photo_gallery.services.jobs.colorize', side_effect=ColorizationError('timeout'))
    def test_failure_keeps_previous_result(self, call):
        self.photo.colorized = jpeg()
        self.photo.save()
        self.client.post(self.start, {'regenerate': '1'})
        run_one()
        self.photo.refresh_from_db()
        self.assertEqual(bytes(self.photo.colorized), jpeg())
        self.assertEqual(ColorizationJob.objects.get().error_code, 'timeout')
        self.assertEqual(self.client.post(self.start, {'regenerate': '1'}).status_code, 202)

    @patch('photo_gallery.services.jobs.colorize', return_value=(jpeg(), 'test'))
    def test_expired_reservation_recovered(self, call):
        job = self.photo.colorization_jobs.create(status='running', attempts=1, lease_until=timezone.now() - timedelta(seconds=1))
        run_one()
        job.refresh_from_db()
        self.assertEqual(job.status, 'succeeded')
        self.assertEqual(job.attempts, 2)

    @patch('photo_gallery.services.jobs.colorize')
    def test_deleted_photo_discards_result(self, call):
        self.client.post(self.start)
        def deleted(_):
            self.photo.delete()
            return jpeg(), 'test'
        call.side_effect = deleted
        run_one()
        self.assertFalse(ColorizationJob.objects.exists())

    @patch('photo_gallery.services.jobs.colorize')
    def test_stale_worker_cannot_save(self, call):
        self.client.post(self.start)
        def expired(_):
            ColorizationJob.objects.update(reservation=None, status='failed')
            return jpeg(), 'test'
        call.side_effect = expired
        run_one()
        self.photo.refresh_from_db()
        self.assertIsNone(self.photo.colorized)

    def test_edit_and_gallery_render(self):
        self.assertContains(self.client.get(f'/{self.photo.pk}'), 'colorization-panel')
        self.assertContains(self.client.get(f'/{self.photo.pk}/edit'), 'photo-form')
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_upload_stores_one_face_per_annotation(self):
        import json
        from django.core.files.uploadedfile import SimpleUploadedFile
        annotation = {'body': [{'purpose': 'name', 'value': 'Anna'}, {'purpose': 'lastName', 'value': 'Test'}], 'target': {'selector': {'value': 'xywh=pixel:0,0,4,4'}}}
        response = self.client.post('/add', {'image': SimpleUploadedFile('scan.jpg', jpeg(), content_type='image/jpeg'), 'description': 'Uploaded', 'tags': '#test', 'additional_data': json.dumps([annotation])})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photographic.objects.get(description='Uploaded').learning_faces.count(), 1)

    def test_database_rejects_two_active_jobs(self):
        from django.db import IntegrityError, transaction
        self.photo.colorization_jobs.create()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.photo.colorization_jobs.create(status='running')

    @patch('photo_gallery.services.jobs.colorize')
    def test_exhausted_reservation_fails_without_inference(self, call):
        job = self.photo.colorization_jobs.create(status='running', attempts=2, lease_until=timezone.now() - timedelta(seconds=1))
        self.assertFalse(run_one())
        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        call.assert_not_called()


from django.test import TransactionTestCase


class ConcurrentJobTests(TransactionTestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=jpeg(), width=8, height=6, format='JPEG')

    def test_simultaneous_clicks_create_one_job(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        barrier = Barrier(2)
        def start():
            try:
                barrier.wait(timeout=5)
                return Client().post(f'/{self.photo.pk}/colorize').json()['job_id']
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as executor:
            ids = list(executor.map(lambda _: start(), range(2)))
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(ColorizationJob.objects.count(), 1)

    def test_two_workers_do_not_process_same_job(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        from django.db import connections
        started, release = Event(), Event()
        self.photo.colorization_jobs.create()
        def inference(_):
            started.set()
            if not release.wait(timeout=10):
                raise RuntimeError('Test synchronization failed')
            return jpeg(), 'test'
        def first_worker():
            try:
                return run_one()
            finally:
                connections.close_all()
        with patch('photo_gallery.services.jobs.colorize', side_effect=inference) as call:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(first_worker)
                try:
                    self.assertTrue(started.wait(timeout=5))
                    self.assertFalse(run_one())
                finally:
                    release.set()
                self.assertTrue(future.result(timeout=5))
            self.assertEqual(call.call_count, 1)
        self.assertEqual(ColorizationJob.objects.get().status, 'succeeded')


class WorkerReadinessTests(SimpleTestCase):
    @patch('photo_gallery.management.commands.colorization_worker.run_one')
    @patch('photo_gallery.management.commands.colorization_worker.requests.get')
    def test_unavailable_model_does_not_consume_jobs(self, get, run):
        from django.core.management import call_command
        get.side_effect = requests.ConnectionError()
        call_command('colorization_worker', once=True, stdout=StringIO())
        run.assert_not_called()

    @patch('photo_gallery.management.commands.colorization_worker.run_one', return_value=False)
    @patch('photo_gallery.management.commands.colorization_worker.requests.get')
    def test_ready_model_allows_processing(self, get, run):
        from django.core.management import call_command
        response = Mock(status_code=200)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        get.return_value = response
        call_command('colorization_worker', once=True)
        run.assert_called_once_with()
