"""Opt-in smoke test against an already running, real DDColor service."""
from io import BytesIO
import os
import unittest
from PIL import Image
from django.test import TestCase
from .models import Photographic, Person, LearningPhotoFace, Tag
from .services.jobs import run_one


@unittest.skipUnless(os.getenv('DDCOLOR_LIVE_TEST') == '1', 'Requires a running DDColor model')
class LiveColorizationTest(TestCase):
    def test_saved_photo_can_be_colorized_and_downloaded(self):
        stream = BytesIO()
        Image.new('L', (64, 48), 128).save(stream, 'JPEG')
        original = stream.getvalue()
        photo = Photographic.objects.create(awers=original, width=64, height=48, format='JPEG', description='Live smoke test')
        tag = Tag.objects.create(keyword='smoke')
        photo.tags.add(tag)
        person = Person.objects.create(name='Test', surname='Person')
        face = LearningPhotoFace.objects.create(face=original, photographicid=photo, personid=person, coordinates=[0, 0, 32, 24])
        self.assertEqual(self.client.post(f'/{photo.pk}/colorize').status_code, 202)
        self.assertTrue(run_one())
        status = self.client.get(f'/{photo.pk}/colorization').json()
        self.assertEqual(status['status'], 'succeeded', status)
        photo.refresh_from_db()
        face.refresh_from_db()
        self.assertEqual(bytes(photo.awers), original)
        self.assertEqual(face.personid_id, person.pk)
        self.assertEqual(face.coordinates, [0, 0, 32, 24])
        self.assertEqual(list(photo.tags.values_list('pk', flat=True)), [tag.pk])
        response = self.client.get(f'/{photo.pk}/colorized?download=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        with Image.open(BytesIO(response.content)) as result:
            self.assertEqual(result.size, (64, 48))
            result.load()
