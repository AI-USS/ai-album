import json
from unittest.mock import patch
from django.test import TestCase
from .models import Person, Photographic
from .test_ui import jpeg


class PeopleLabelTests(TestCase):
    def setUp(self):
        self.photo = Photographic.objects.create(awers=jpeg(), width=16, height=16, format='JPEG')
        self.person = Person.objects.create(name='Anna', surname='Test')
        self.face = self.photo.learning_faces.create(face=jpeg(), personid=self.person, coordinates=[0, 0, 8, 8])

    def annotation(self, values):
        return {'id': self.face.pk, 'type': 'Annotation', 'body': [{'purpose': key, 'value': value} for key, value in values.items()], 'target': {'selector': {'value': 'xywh=pixel:0,0,8,8'}}}

    def save(self, values):
        return self.client.post(f'/{self.photo.pk}/edit', {'description': '', 'djtags': '', 'additional_data': json.dumps([self.annotation(values)])})

    @patch('photo_gallery.views.rebuild_face_encodings')
    def test_existing_person_uses_id_even_for_duplicate_names_and_retrains(self, rebuild):
        other = Person.objects.create(name='Anna', surname='Test')
        with self.captureOnCommitCallbacks(execute=True):
            response = self.save({'personId': other.pk, 'name': 'Ignored', 'lastName': 'Ignored', 'newPerson': False})
            rebuild.assert_not_called()
        self.assertEqual(response.status_code, 302)
        self.face.refresh_from_db()
        self.assertEqual(self.face.personid_id, other.pk)
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, 'Anna')
        self.assertEqual(Person.objects.count(), 2)
        rebuild.assert_called_once_with()

    def test_explicit_new_person_and_unassignment(self):
        self.assertEqual(self.save({'personId': None, 'name': 'Jan', 'lastName': 'Nowy', 'newPerson': True}).status_code, 302)
        self.face.refresh_from_db()
        self.assertEqual(self.face.personid.name, 'Jan')
        self.assertEqual(self.save({'personId': None, 'name': None, 'lastName': None, 'newPerson': False}).status_code, 302)
        self.face.refresh_from_db()
        self.assertIsNone(self.face.personid_id)
        self.assertTrue(Person.objects.filter(name='Jan').exists())

    def test_invalid_person_or_partial_name_is_rejected(self):
        for values in [{'personId': 2147483647}, {'personId': True}, {'name': 'Anna', 'lastName': None}]:
            with self.subTest(values=values):
                self.assertEqual(self.save(values).status_code, 200)
                self.face.refresh_from_db()
                self.assertEqual(self.face.personid_id, self.person.pk)

    @patch('photo_gallery.views.rebuild_face_encodings')
    def test_removing_face_also_retrains(self, rebuild):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f'/{self.photo.pk}/edit', {'additional_data': '[]'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.photo.learning_faces.exists())
        rebuild.assert_called_once_with()

    def test_context_includes_person_ids_and_picker_data(self):
        response = self.client.get(f'/{self.photo.pk}/edit')
        self.assertContains(response, 'id="face-list"')
        self.assertEqual(response.context['initial_annotations'][0]['body'][-1]['value'], self.person.pk)
        self.assertEqual(response.context['available_people'][0]['id'], self.person.pk)
