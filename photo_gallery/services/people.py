"""Resolve face labels without changing another person's identity."""
from photo_gallery.models import Person


def resolve_person(bodies):
    values = {body['purpose']: body['value'] for body in bodies}
    person_id = values.get('personId')
    if person_id is not None:
        return Person.objects.get(pk=person_id)
    name = (values.get('name') or '').strip()
    surname = (values.get('lastName') or '').strip()
    if not name or not surname:
        return None
    if values.get('newPerson') is True:
        return Person.objects.create(name=name, surname=surname)
    return Person.objects.get_or_create(name=name, surname=surname)[0]
