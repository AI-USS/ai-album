from io import BytesIO
import json
import pickle
import sys
import types
from unittest.mock import Mock, patch

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase

from .models import FaceEncoding, LearningPhotoFace, Person, Photographic
from .services.face_training import rebuild_face_encodings


def image_data():
    data = BytesIO()
    Image.new('RGB', (16, 16), 'gray').save(data, 'JPEG')
    return data.getvalue()


class TrainingTriggerTests(TestCase):
    def upload(self):
        annotation = {
            'body': [{'purpose': 'name', 'value': 'Anna'}, {'purpose': 'lastName', 'value': 'Test'}],
            'target': {'selector': {'value': 'xywh=pixel:0,0,16,16'}},
        }
        return self.client.post('/add', {
            'image': SimpleUploadedFile('photo.jpg', image_data(), content_type='image/jpeg'),
            'description': 'Automatic training', 'tags': '',
            'additional_data': json.dumps([annotation]),
        })

    @patch('photo_gallery.views.rebuild_face_encodings')
    def test_trigger_runs_after_all_annotations_are_saved(self, rebuild):
        def check_saved_data():
            face = LearningPhotoFace.objects.get()
            self.assertEqual(face.personid.name, 'Anna')
            self.assertEqual(face.photographicid.description, 'Automatic training')
        rebuild.side_effect = check_saved_data
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.upload()
            rebuild.assert_not_called()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(callbacks), 1)
        rebuild.assert_called_once_with()

    @patch('photo_gallery.views.rebuild_face_encodings')
    def test_failed_or_rolled_back_upload_does_not_trigger_training(self, rebuild):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.assertEqual(self.client.post('/add', {}).status_code, 200)
            with transaction.atomic():
                self.upload()
                transaction.set_rollback(True)
        self.assertEqual(callbacks, [])
        rebuild.assert_not_called()
        self.assertFalse(Photographic.objects.exists())

    def test_training_error_does_not_fail_successful_upload(self):
        def fail_training():
            raise RuntimeError('Training failed')
        with patch('photo_gallery.views.rebuild_face_encodings', new=fail_training):
            with self.assertLogs('django.test', level='ERROR'):
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.upload()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photographic.objects.count(), 1)
        self.assertEqual(LearningPhotoFace.objects.count(), 1)

    @patch('photo_gallery.views.rebuild_face_encodings')
    def test_manual_button_uses_same_rebuild(self, rebuild):
        self.assertEqual(self.client.post('/learn').status_code, 302)
        rebuild.assert_called_once_with()


class FaceIndexTests(TestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=image_data(), width=16, height=16, format='JPEG')
        self.person = Person.objects.create(name='Anna', surname='Test')
        self.photo.learning_faces.create(face=image_data(), personid=self.person, coordinates=[0, 0, 16, 16])
        self.photo.learning_faces.create(face=image_data(), coordinates=[0, 0, 16, 16])
        self.recognizer = types.ModuleType('face_recognition')
        self.recognizer.load_image_file = Mock(return_value='image')
        self.recognizer.face_locations = Mock(return_value=['location'])
        self.recognizer.face_encodings = Mock(return_value=[[0.1, 0.2]])

    def test_complete_index_uses_labelled_faces_only(self):
        with patch.dict(sys.modules, {'face_recognition': self.recognizer}):
            result = rebuild_face_encodings()
        self.assertEqual(pickle.loads(bytes(result.file)), {'persons_id': [self.person.pk], 'encodings': [[0.1, 0.2]]})
        self.recognizer.face_encodings.assert_called_once_with('image', ['location'])

    def test_training_failure_keeps_previous_index(self):
        previous = FaceEncoding.objects.create(file=pickle.dumps({'persons_id': [], 'encodings': []}))
        self.recognizer.face_encodings.side_effect = RuntimeError('Training failed')
        with patch.dict(sys.modules, {'face_recognition': self.recognizer}):
            with self.assertRaisesMessage(RuntimeError, 'Training failed'):
                rebuild_face_encodings()
        self.assertEqual(FaceEncoding.objects.get().pk, previous.pk)
