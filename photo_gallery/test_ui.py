from io import BytesIO
import json
from unittest.mock import patch
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from .forms import parse_tags
from .models import Photographic, Tag, Person


def jpeg():
    buffer = BytesIO()
    Image.new('RGB', (16, 16)).save(buffer, 'JPEG')
    return buffer.getvalue()


class AlbumUiTests(TestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=jpeg(), format='JPEG', width=16, height=16, description='Wakacje')
        self.other = Photographic.objects.create(awers=jpeg(), format='JPEG', width=16, height=16)
        self.person = Person.objects.create(name='Anna', surname='Test')
        self.photo.learning_faces.create(face=jpeg(), personid=self.person, coordinates=[0, 0, 8, 8])
        self.tag = Tag.objects.create(keyword='rodzina')
        self.photo.tags.add(self.tag)

    def test_first_filter_and_selected_state(self):
        response = self.client.get('/', {'people': self.person.pk, 'tags': self.tag.pk})
        self.assertEqual(list(response.context['photographics']), [self.photo])
        self.assertContains(response, f'value="{self.person.pk}" checked')
        self.assertContains(response, 'Wyczyść filtry')

    def test_invalid_filter_values_do_not_crash(self):
        response = self.client.get('/', {'people': ['', 'abc', '-1', '9999999999999999999999999999']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['photographics']), 2)

    def test_empty_filter_results_and_no_fake_dates(self):
        response = self.client.get('/', {'people': 2147483647})
        self.assertContains(response, 'Brak zdjęć dla tych filtrów')
        self.assertNotContains(response, '2024-08-20')

    def test_plain_and_legacy_tags(self):
        self.assertEqual(parse_tags('rodzina, wakacje,rodzina'), ['rodzina', 'wakacje'])
        self.assertEqual(parse_tags('#rodzina# wakacje '), ['rodzina', 'wakacje'])

    def test_invalid_annotations_display_error_without_saving(self):
        response = self.client.post('/add', {'image': SimpleUploadedFile('test.jpg', jpeg(), content_type='image/jpeg'), 'additional_data': 'invalid'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sprawdź dane przed zapisaniem')
        self.assertEqual(Photographic.objects.count(), 2)

    def test_edit_tags_reverse_and_confirmation(self):
        annotations = self.client.get(f'/{self.photo.pk}/edit').context['initial_annotations']
        response = self.client.post(f'/{self.photo.pk}/edit', {
            'description': 'Nowy opis', 'djtags': 'wakacje, rodzina',
            'additional_data': json.dumps(annotations),
            'rewers_image': SimpleUploadedFile('back.jpg', jpeg(), content_type='image/jpeg'),
        }, follow=True)
        self.assertContains(response, 'Zmiany zapisane.')
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.description, 'Nowy opis')
        self.assertEqual(set(self.photo.tags.values_list('keyword', flat=True)), {'wakacje', 'rodzina'})
        self.assertEqual(bytes(self.photo.rewers), jpeg())
        self.assertEqual(self.photo.learning_faces.get().personid, self.person)

    def test_foreign_face_id_is_rejected(self):
        foreign = self.other.learning_faces.create(face=jpeg(), coordinates=[0, 0, 8, 8])
        annotations = self.client.get(f'/{self.photo.pk}/edit').context['initial_annotations']
        annotations[0]['id'] = foreign.pk
        response = self.client.post(f'/{self.photo.pk}/edit', {'description': 'Bad', 'additional_data': json.dumps(annotations)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jedno z oznaczeń jest nieaktualne')
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.description, 'Wakacje')

    def test_delete_confirmation_and_feedback(self):
        response = self.client.get(f'/{self.other.pk}/delete')
        self.assertContains(response, 'Anuluj')
        response = self.client.post(f'/{self.other.pk}/delete', follow=True)
        self.assertContains(response, 'Zdjęcie zostało usunięte.')
        self.assertFalse(Photographic.objects.filter(pk=self.other.pk).exists())


class PhotoViewerTests(TestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=jpeg(), format='JPEG', width=16, height=16, description='Podgląd')

    def test_gallery_links_to_viewer_and_has_no_delete_menu(self):
        response = self.client.get('/')
        self.assertContains(response, f'href="/{self.photo.pk}"')
        self.assertNotContains(response, 'Więcej')
        self.assertNotContains(response, f'/{self.photo.pk}/delete')

    def test_viewer_exposes_actions_without_edit_form(self):
        response = self.client.get(f'/{self.photo.pk}')
        self.assertContains(response, 'Wersja kolorowa')
        self.assertContains(response, f'/{self.photo.pk}/delete')
        self.assertContains(response, f'/{self.photo.pk}/edit')
        self.assertContains(response, 'Pobierz oryginał')
        self.assertNotContains(response, 'id="photo-form"')
        self.assertEqual(self.client.get('/2147483647').status_code, 404)

    def test_sources_are_correct_and_downloadable(self):
        original = self.client.get(f'/{self.photo.pk}/original?download=1')
        self.assertEqual(original.content, jpeg())
        self.assertEqual(original['Content-Type'], 'image/jpeg')
        self.assertIn('attachment', original['Content-Disposition'])
        self.assertEqual(self.client.get(f'/{self.photo.pk}/reverse').status_code, 404)
        self.photo.rewers = jpeg()
        self.photo.colorized = jpeg()
        self.photo.save()
        for path in ('reverse', 'colorized'):
            response = self.client.get(f'/{self.photo.pk}/{path}?download=1')
            self.assertEqual(response.content, jpeg())
            self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(self.client.post(f'/{self.photo.pk}/original').status_code, 405)

    def test_detail_does_not_change_data_and_deduplicates_people(self):
        person = Person.objects.create(name='Anna', surname='Test')
        for _ in range(2):
            self.photo.learning_faces.create(face=jpeg(), personid=person, coordinates=[0, 0, 8, 8])
        response = self.client.get(f'/{self.photo.pk}')
        self.assertEqual(response.context['people'], [person])
        self.assertEqual(self.photo.learning_faces.count(), 2)
        self.photo.refresh_from_db()
        self.assertIsNone(self.photo.colorized)
