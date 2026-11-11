from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect
from .models import Photographic, Tag, Person, LearningPhotoFace, FaceEncoding
from django.views.generic.edit import DeleteView, UpdateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import AddPhotoForm, ModelLearnForm, EditPhotoForm, parse_tags
from collections import Counter
from django.urls import reverse_lazy
from PIL import Image
import pickle
import json
import io
import base64
from django.db.models import BooleanField, Case, When, Q, Prefetch
from django.contrib import messages
import logging
from django.db import transaction
from .services.face_training import rebuild_face_encodings
from .services.people import resolve_person




def home(request):
    def selected_ids(name):
        values = set()
        for raw in request.GET.getlist(name):
            try:
                value = int(raw)
                if 0 < value <= 2147483647:
                    values.add(value)
            except (ValueError, TypeError):
                pass
        return sorted(values)

    selected_tags = selected_ids('tags')
    selected_people = selected_ids('people')
    photos = Photographic.objects.all().order_by('-id')
    if selected_tags:
        photos = photos.filter(tags__id__in=selected_tags)
    if selected_people:
        photos = photos.filter(learning_faces__personid_id__in=selected_people)
    return render(request, 'home.html', {
        'photographics': photos.distinct(),
        'available_tags': Tag.objects.order_by('keyword'),
        'available_people': Person.objects.order_by('surname', 'name'),
        'selected_tags': selected_tags, 'selected_people': selected_people,
    })


@transaction.atomic
def upload_image(request):
    if request.method == 'POST':
        form = AddPhotoForm(request.POST, request.FILES)
        if form.is_valid():

            file = form.cleaned_data['image']
            description = form.cleaned_data['description']
            tags = form.cleaned_data['tags']
            additional = form.cleaned_data['additional_data']

            image_data = file.read()

            additional = json.loads(additional)

            image_model = Photographic.objects.create(
                                    description=description,
                                    awers=image_data,
                                    format=file.image.format,
                                    width=file.image.size[0],
                                    height=file.image.size[1]
                                       )


            for tag in parse_tags(tags):
                tag_object, _ = Tag.objects.get_or_create(keyword=tag)
                image_model.tags.add(tag_object)

            for annotation in additional:
                person = resolve_person(annotation['body'])
                x, y, width, height = map(float, annotation['target']['selector']['value'].split(':', 1)[1].split(','))
                coords = [x, y, x + width, y + height]
                with Image.open(io.BytesIO(image_data)) as source:
                    buffer = io.BytesIO()
                    source.crop(coords).save(buffer, format=image_model.format)
                image_model.learning_faces.create(face=buffer.getvalue(), personid=person, coordinates=coords)

            # Run only after the photo and all annotations have committed.
            # A training failure must not turn a successful upload into an error.
            def update_recognition():
                try:
                    rebuild_face_encodings()
                except Exception:
                    messages.warning(request, 'Zdjęcie zapisane. Nie udało się zaktualizować rozpoznawania osób. Możesz ponowić aktualizację w dodatkowych działaniach.')
                    raise
                else:
                    messages.success(request, 'Zdjęcie zapisane. Rozpoznawanie osób zostało zaktualizowane.')
            transaction.on_commit(update_recognition, robust=True)
            return redirect('photographic_detail', pk=image_model.pk)
    else:
        form = AddPhotoForm()

    return render(request, 'add.html', {'form': form, 'initial_tags': parse_tags(request.POST.get('tags', '')), 'available_people': list(Person.objects.order_by('surname', 'name', 'pk').values('id', 'name', 'surname'))})


@csrf_exempt
def recognize_face_at_photo(request):
    import face_recognition
    if request.method == "POST":
        file = request.FILES.get("file")
        input_image = face_recognition.load_image_file(file)
        input_face_locations = face_recognition.face_locations(input_image)
        persons = {}
        person_count = 0
        loaded_encodings = FaceEncoding.objects.last()

        if loaded_encodings:
            
            for photo in [file]:
                    
                loaded_encodings = pickle.loads(loaded_encodings.file)

                input_image = face_recognition.load_image_file(photo)
                input_face_locations = face_recognition.face_locations(input_image, model="hog")
                input_face_encodings = face_recognition.face_encodings(input_image, input_face_locations)

                for bounding_box, unknown_encoding in zip(input_face_locations, input_face_encodings):
                    id = _recognize_face(unknown_encoding, loaded_encodings)
                    if id:
                        person = Person.objects.filter(id=id)[0]
                        recognized = True
                        name = person.name
                        last_name = person.surname
                    else:
                        id = None
                        recognized = False
                        name = None
                        last_name = None
                    persons[person_count] = {"recognized": recognized, "id": id, "name": name, "last_name": last_name, "coords": bounding_box}
                    person_count += 1
                return JsonResponse(persons)
        else:
            for face in input_face_locations:
                persons[person_count] = {"recognized": False, "id": None, "name": None, "last_name": None, "coords": face}
                person_count += 1
            return JsonResponse(persons)  
    return JsonResponse({}, status=400)


class SearchPageView(TemplateView):
    template_name = "search.html"


def learn(request):
    if request.method == 'POST' and ModelLearnForm(request.POST).is_valid():
        try:
            rebuild_face_encodings()
            messages.success(request, 'Rozpoznawanie osób zostało zaktualizowane.')
        except Exception:
            logging.getLogger(__name__).exception('Manual face index rebuild failed')
            messages.error(request, 'Nie udało się odświeżyć rozpoznawania. Spróbuj ponownie później.')
    return redirect('home')



def _recognize_face(unknown_encoding, loaded_encodings):
    import face_recognition
    boolean_matches = face_recognition.compare_faces(
        loaded_encodings["encodings"], unknown_encoding
    )
    votes = Counter(
        id
        for match, id in zip(boolean_matches, loaded_encodings["persons_id"])
        if match
    )
    if votes:
        return votes.most_common(1)[0][0]

    
class PhotographicDetailView(DetailView):
    model = Photographic
    template_name = 'photographic_detail.html'

    def get_queryset(self):
        from .colorization_views import photo_query
        return photo_query().annotate(
            has_reverse=Case(When(Q(rewers__isnull=False) & ~Q(rewers=b''), then=True), default=False, output_field=BooleanField()),
        ).prefetch_related('tags', Prefetch('learning_faces', queryset=LearningPhotoFace.objects.select_related('personid').defer('face')))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        people = {face.personid_id: face.personid for face in self.object.learning_faces.all() if face.personid_id}
        context['people'] = sorted(people.values(), key=lambda person: (person.surname, person.name))
        context['unknown_faces'] = sum(face.personid_id is None for face in self.object.learning_faces.all())
        context['previous_photo'] = Photographic.objects.filter(pk__lt=self.object.pk).order_by('-pk').only('id').first()
        context['next_photo'] = Photographic.objects.filter(pk__gt=self.object.pk).order_by('pk').only('id').first()
        return context


class PhotographicDeleteView(DeleteView):
    model = Photographic
    template_name = "photographic_delete.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Zdjęcie zostało usunięte.')
        return response


class PhotographicEditView(UpdateView):
    model = Photographic
    form_class = EditPhotoForm
    template_name = "photographic_edit.html"
    def get_success_url(self):
        return reverse_lazy('photographic_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        form = context['form']
        context['initial_tags'] = parse_tags(form.data.get('djtags', '')) if form.is_bound else list(obj.tags.values_list('keyword', flat=True))
        annotations = []
        for face in obj.learning_faces.select_related('personid'):
            x, y, right, bottom = face.coordinates
            annotations.append({
                'id': face.pk, 'type': 'Annotation',
                'body': [
                    {'type': 'TextualBody', 'purpose': 'name', 'value': face.personid.name if face.personid else None},
                    {'type': 'TextualBody', 'purpose': 'lastName', 'value': face.personid.surname if face.personid else None},
                    {'type': 'TextualBody', 'purpose': 'newPerson', 'value': False},
                    {'type': 'TextualBody', 'purpose': 'personId', 'value': face.personid_id},
                ],
                'target': {'selector': {'type': 'FragmentSelector', 'conformsTo': 'http://www.w3.org/TR/media-frags/', 'value': f'xywh=pixel:{x},{y},{right-x},{bottom-y}'}},
            })
        context['available_people'] = list(Person.objects.order_by('surname', 'name', 'pk').values('id', 'name', 'surname'))
        context['initial_annotations'] = annotations
        context['rewers_data'] = base64.b64encode(obj.rewers).decode() if obj.rewers else None
        return context
    

    @transaction.atomic
    def form_valid(self, form):
        annotations = json.loads(form.cleaned_data['additional_data'])
        existing = {face.pk: face for face in self.object.learning_faces.all()}
        for annotation in annotations:
            if isinstance(annotation.get('id'), int) and annotation['id'] not in existing:
                form.add_error('additional_data', 'Jedno z oznaczeń jest nieaktualne. Odśwież zdjęcie i spróbuj ponownie.')
                return self.form_invalid(form)
        self.object = form.save(commit=False)
        self.object.tags.set([Tag.objects.get_or_create(keyword=tag)[0] for tag in parse_tags(form.cleaned_data['djtags'])])
        retained = []
        for annotation in annotations:
            person = resolve_person(annotation['body'])
            x, y, width, height = map(float, annotation['target']['selector']['value'].split(':', 1)[1].split(','))
            coords = [x, y, x + width, y + height]
            with Image.open(io.BytesIO(bytes(self.object.awers))) as source:
                crop = source.crop(coords)
                buffer = io.BytesIO()
                crop.save(buffer, format=self.object.format)
            values = {'face': buffer.getvalue(), 'personid': person, 'coordinates': coords}
            face_id = annotation.get('id')
            if isinstance(face_id, int):
                self.object.learning_faces.filter(pk=face_id).update(**values)
                retained.append(face_id)
            else:
                retained.append(self.object.learning_faces.create(**values).pk)
        self.object.learning_faces.exclude(pk__in=retained).delete()
        rewers = form.cleaned_data.get('rewers_image')
        if rewers:
            self.object.rewers = rewers.read()
        self.object.save()
        def update_recognition():
            try:
                rebuild_face_encodings()
            except Exception:
                messages.warning(self.request, 'Zmiany zapisane. Aktualizacja rozpoznawania nie powiodła się; możesz ponowić ją w dodatkowych działaniach.')
                raise
        transaction.on_commit(update_recognition, robust=True)
        messages.success(self.request, 'Zmiany zapisane.')
        return super().form_valid(form)
