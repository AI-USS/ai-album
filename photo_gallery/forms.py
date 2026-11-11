import json
import math
from django import forms
from .models import Photographic, Person


def parse_tags(value):
    import re
    return list(dict.fromkeys(tag.strip() for tag in re.split(r'[#,\n]', value) if tag.strip()))


class AnnotationFormMixin:
    def clean_additional_data(self):
        raw = self.cleaned_data.get('additional_data') or '[]'
        try:
            annotations = json.loads(raw)
            if not isinstance(annotations, list):
                raise ValueError
            for annotation in annotations:
                bodies = annotation['body']
                selector = annotation['target']['selector']['value']
                if not isinstance(bodies, list) or not bodies:
                    raise ValueError
                for body in bodies:
                    if not isinstance(body, dict) or 'purpose' not in body or 'value' not in body:
                        raise ValueError
                    if body['purpose'] in ('name', 'lastName') and body['value'] is not None:
                        if not isinstance(body['value'], str) or len(body['value']) > 100:
                            raise ValueError
                values = {body['purpose']: body['value'] for body in bodies}
                person_id = values.get('personId')
                if person_id is not None and (type(person_id) is not int or not Person.objects.filter(pk=person_id).exists()):
                    raise forms.ValidationError('Wybrana osoba już nie istnieje. Wybierz osobę ponownie.')
                name, surname = (values.get('name') or '').strip(), (values.get('lastName') or '').strip()
                if person_id is None and bool(name) != bool(surname):
                    raise forms.ValidationError('Podaj imię i nazwisko nowej osoby albo pozostaw twarz bez podpisu.')
                if person_id is None and name and surname and values.get('newPerson') is not True and Person.objects.filter(name=name, surname=surname).count() > 1:
                    raise forms.ValidationError('Kilka osób ma takie samo imię i nazwisko. Wybierz konkretną osobę z listy.')
                if not isinstance(selector, str) or not selector.startswith('xywh=pixel:'):
                    raise ValueError
                coords = [float(value) for value in selector.split(':', 1)[1].split(',')]
                if len(coords) != 4 or not all(math.isfinite(value) for value in coords):
                    raise ValueError
                if min(coords[:2]) < 0 or min(coords[2:]) <= 0:
                    raise ValueError
                source = self.cleaned_data.get('image')
                dimensions = source.image.size if source else ((self.instance.width, self.instance.height) if getattr(self, 'instance', None) else None)
                if dimensions and (coords[0] + coords[2] > dimensions[0] or coords[1] + coords[3] > dimensions[1]):
                    raise ValueError
            return json.dumps(annotations)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise forms.ValidationError('Nie udało się odczytać oznaczeń twarzy. Sprawdź zdjęcie i spróbuj ponownie.')

    def clean(self):
        data = super().clean()
        for name in ('tags', 'djtags'):
            if name in data and any(len(tag) > 100 for tag in parse_tags(data[name])):
                self.add_error(name, 'Pojedynczy tag może mieć najwyżej 100 znaków.')
        return data


class AddPhotoForm(AnnotationFormMixin, forms.Form):
    image = forms.ImageField(label='Zdjęcie', widget=forms.ClearableFileInput(attrs={'id': 'awers', 'accept': 'image/*'}))
    description = forms.CharField(label='Opis zdjęcia', max_length=255, required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Np. Rodzinne wakacje nad morzem'}))
    tags = forms.CharField(label='Tagi', max_length=255, required=False, widget=forms.HiddenInput(attrs={'id': 'djtags'}))
    additional_data = forms.CharField(label='Oznaczenia twarzy', required=False, widget=forms.HiddenInput(attrs={'id': 'additional_data'}))


class ModelLearnForm(forms.Form):
    pass


class EditPhotoForm(AnnotationFormMixin, forms.ModelForm):
    rewers_image = forms.ImageField(label='Tył zdjęcia', required=False, widget=forms.ClearableFileInput(attrs={'id': 'rewers-file', 'accept': 'image/*'}))
    description = forms.CharField(label='Opis zdjęcia', max_length=255, required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dodaj opis tego wspomnienia'}))
    djtags = forms.CharField(label='Tagi', max_length=255, required=False, widget=forms.HiddenInput(attrs={'id': 'djtags'}))
    additional_data = forms.CharField(label='Oznaczenia twarzy', required=False, widget=forms.HiddenInput(attrs={'id': 'additional_data'}))

    class Meta:
        model = Photographic
        fields = ('rewers_image', 'description', 'djtags')
