"""Rebuild the recognition index from all saved, labelled face crops."""
from io import BytesIO
import pickle

from django.db import connection, transaction
from photo_gallery.models import FaceEncoding, LearningPhotoFace


@transaction.atomic
def rebuild_face_encodings():
    import face_recognition

    # Serialize rebuilds across web processes. Read the dataset only after the
    # lock is acquired so an older rebuild cannot overwrite a newer snapshot.
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(%s)', [724108291])

    persons_id, encodings = [], []
    faces = LearningPhotoFace.objects.exclude(personid__isnull=True).order_by('pk')
    for face in faces.iterator():
        image = face_recognition.load_image_file(BytesIO(bytes(face.face)))
        locations = face_recognition.face_locations(image, model='hog')
        for encoding in face_recognition.face_encodings(image, locations):
            persons_id.append(face.personid_id)
            encodings.append(encoding)

    # Publish only a complete index. On failure the previous index remains valid.
    return FaceEncoding.objects.create(
        file=pickle.dumps({'persons_id': persons_id, 'encodings': encodings}),
    )
