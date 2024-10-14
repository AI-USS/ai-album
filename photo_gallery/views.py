from django.forms.models import BaseModelForm
from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from .models import Photographic, Tag, Person, LearningPhotoFace, FaceEncoding
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, UpdateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import AddPhotoForm, ModelLearnForm, EditPhotoForm
from collections import Counter
from django.urls import reverse_lazy
import face_recognition
from PIL import Image
import pickle
import json
import io
import base64
from django.db.models import Q




def home(request):
    from base64 import b64encode
    images = Photographic.objects.all().order_by('-id')[:12]
    for image in images:
        image.awers = b64encode(image.awers).decode('utf-8')
    
    available_tags = Tag.objects.all()
    available_people = Person.objects.all()

    photographic_queryset = Photographic.objects.all()

    selected_tags = request.GET.getlist('tags')[1:]
    selected_people = request.GET.getlist('people')[1:]

    selected_tags = list(map(int, selected_tags))
    selected_people = list(map(int, selected_people))

    if selected_tags:
        photographic_queryset = photographic_queryset.filter(tags__id__in=selected_tags).distinct()

    if selected_people:
        queries = Q()
        for person_id in selected_people:
            queries |= Q(learning_faces__personid__id=person_id)
        photographic_queryset = photographic_queryset.filter(queries).distinct()

    context = {
        'photographics': photographic_queryset,
        'available_tags': available_tags,
        'available_people': available_people,
        'selected_tags': selected_tags,
        'selected_people': selected_people
    }

    return render(request, 'home.html', context)


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


            tags = tags.split("#")
            for tag in tags:
                if tag is not "":
                    tagsORM, created = Tag.objects.get_or_create(keyword=tag)
                    image_model.tags.add(tagsORM)


            for annotation in additional:
                for info in annotation["body"]:
                    if info["purpose"] == "name":
                        name = info["value"]
                    if info["purpose"] == "lastName":
                        last_name = info["value"]
                    coords = annotation["target"]["selector"]["value"].split(':')[1].split(",")
                    coords = list(map(float, coords))
                    coords = [coords[0],coords[1],coords[0] + coords[2],coords[1] + coords[3]]


                    opening_image_file = Image.open(file)
                    cutted_face = opening_image_file.crop(coords)
                    img_byte_arr = io.BytesIO()
                    cutted_face.save(img_byte_arr, format=file.image.format)
                    img_byte_arr = img_byte_arr.getvalue()

                if name is not None and last_name is not None:
                    person_model, created = Person.objects.get_or_create(
                        name=name,
                        surname=last_name
                    )
                    person_model.save()

                    LearningPhotoFace.objects.create(
                        face=img_byte_arr,
                        personid=person_model,
                        photographicid=image_model,
                        coordinates=coords
                    )
                else:
                    LearningPhotoFace.objects.create(
                        face=img_byte_arr,
                        personid=None,
                        photographicid=image_model,
                        coordinates=coords
                    )


            for annotation in additional:
                for info in annotation["body"]:
                    if info["purpose"] == "name":
                        name = info["value"]
                    if info["purpose"] == "lastName":
                        last_name = info["value"]
                    coords = annotation["target"]["selector"]["value"].split(':')[1].split(",")
                    coords = list(map(float, coords))
                    coords = [coords[0],coords[1],coords[0] + coords[2],coords[1] + coords[3]]


                    opening_image_file = Image.open(file)
                    cutted_face = opening_image_file.crop(coords)
                    img_byte_arr = io.BytesIO()
                    cutted_face.save(img_byte_arr, format=file.image.format)
                    img_byte_arr = img_byte_arr.getvalue()

                if name is not None and last_name is not None:
                    person_model, created = Person.objects.get_or_create(
                        name=name,
                        surname=last_name
                    )
                    person_model.save()

                    LearningPhotoFace.objects.create(
                        face=img_byte_arr,
                        personid=person_model,
                        photographicid=image_model,
                        coordinates=coords
                    )
                else:
                    LearningPhotoFace.objects.create(
                        face=img_byte_arr,
                        personid=None,
                        photographicid=image_model,
                        coordinates=coords
                    )

            return redirect('/')
    else:
        form = AddPhotoForm()

    return render(request, 'add.html', {'form': form})


@csrf_exempt
def recognize_face_at_photo(request):
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
    if request.method == "POST":
        form = ModelLearnForm(request.POST)
        if form.is_valid():
            persons_id = []
            encodings = []
            for photo in LearningPhotoFace.objects.exclude(personid__isnull=True):
                file = io.BytesIO(photo.face)
                person_id = photo.personid.id
                image = face_recognition.load_image_file(file)

                face_locations = face_recognition.face_locations(image, model="hog")
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                for encoding in face_encodings:
                    persons_id.append(person_id)
                    encodings.append(encoding)

            persons_encodings = {"persons_id": persons_id, "encodings": encodings}
            encoding_data = pickle.dumps(persons_encodings)
            FaceEncoding.objects.create(file=encoding_data)

            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = ModelLearnForm()
    return redirect(request.META.get('HTTP_REFERER'))
    


def _recognize_face(unknown_encoding, loaded_encodings):
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

    
class PhotographicDeleteView(DeleteView):
    model = Photographic
    template_name = "photographic_delete.html"
    success_url = reverse_lazy("home")


class PhotographicEditView(UpdateView):
    model = Photographic
    form_class = EditPhotoForm
    template_name = "photographic_edit.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        tags = []
        for tag in obj.tags.all():
            tags.append("#"+tag.keyword)
        context["tags_for_js"] = tags

        face_for_js = {}
        faces = LearningPhotoFace.objects.select_related().filter(photographicid=obj.id)
        for face in faces:
            if face.personid is not None:
                face_for_js[str(face.id)] = {"id": face.id, "name": face.personid.name, "last_name": face.personid.surname, "coords": face.coordinates}
            else:
                face_for_js[str(face.id)] = {"id": face.id, "name": None, "last_name": None, "coords": face.coordinates}
            context["face_for_js"] = json.dumps(face_for_js)
        return context
    

    def form_valid(self, form):
        self.object = form.save(commit=False)
        tags = form.cleaned_data['djtags']
        tags = tags.split("#")
        for tag in self.object.tags.all():
            self.object.tags.remove(tag)
    
        for tag in tags[1:]:
            if tag not in self.object.tags.all():
                tagsORM, created = Tag.objects.get_or_create(keyword=tag)
                self.object.tags.add(tagsORM)
        
        additional = form.cleaned_data['additional_data']
        additional = json.loads(additional)

        faces_id_on_photo = [obj.id for obj in LearningPhotoFace.objects.select_related().filter(photographicid=self.object.id)]
        faces_id_on_annotation = [annotation["id"] for annotation in additional if isinstance(annotation["id"], int)]
        faces_id_from_photo_to_remove = list(set(faces_id_on_photo) - set(faces_id_on_annotation))
        
        for id in faces_id_from_photo_to_remove:
            LearningPhotoFace.objects.filter(id=id).delete()


        for annotation in additional:
            for info in annotation["body"]:
                if info["purpose"] == "name":
                    name = info["value"]
                if info["purpose"] == "lastName":
                    last_name = info["value"]
                if info["purpose"] == "newPerson":
                    is_new_person = info["value"]
                coords = annotation["target"]["selector"]["value"].split(':')[1].split(",")
                coords = list(map(float, coords))
                coords = [coords[0],coords[1],coords[0] + coords[2],coords[1] + coords[3]]
                
            if isinstance(annotation["id"], str):
                opening_image_file = Image.open(io.BytesIO(self.object.awers))
                cutted_face = opening_image_file.crop(coords)
                img_byte_arr = io.BytesIO()
                cutted_face.save(img_byte_arr, format=self.object.format)
                img_byte_arr = img_byte_arr.getvalue()

                if name is not None and last_name is not None:
                    if is_new_person:
                        person_model = Person.objects.create(
                            name=name,
                            surname=last_name
                        )
                        person_model.save()
                    else:
                        person_model = Person.objects.get(name=name, surname=last_name)

                    LearningPhotoFace.objects.create(
                        face=img_byte_arr,
                        personid=person_model,
                        photographicid=self.object,
                        coordinates=coords
                    )
            else:
                to_edit = LearningPhotoFace.objects.filter(id=annotation["id"])[0]
                if to_edit.coordinates != coords:
                    opening_image_file = Image.open(io.BytesIO(self.object.awers))
                    cutted_face = opening_image_file.crop(coords)
                    img_byte_arr = io.BytesIO()
                    cutted_face.save(img_byte_arr, format=self.object.format)
                    img_byte_arr = img_byte_arr.getvalue()

                    LearningPhotoFace.objects.filter(id=to_edit.id).update(coordinates=coords, face=img_byte_arr)
                if to_edit.personid:
                    if is_new_person:
                        person_model = Person.objects.create(
                            name=name,
                            surname=last_name
                        )
                        person_model.save()
                        LearningPhotoFace.objects.filter(id=to_edit.id).update(personid=person_model)
                    else:
                        if to_edit.personid.name != name:
                            Person.objects.filter(id=to_edit.personid.id).update(name=name)
                        if to_edit.personid.surname != last_name:
                            Person.objects.filter(id=to_edit.personid.id).update(surname=last_name)
                elif to_edit.personid is None and name != None and last_name != None:
                    if is_new_person:
                        person_model = Person.objects.create(
                            name=name,
                            surname=last_name
                        )
                        person_model.save()
                    else:
                        person_model = Person.objects.get(name=name, surname=last_name)
                        print(person_model)
                    LearningPhotoFace.objects.filter(id=to_edit.id).update(personid=person_model)
                else:
                    continue

        self.object.save()
        return super().form_valid(form)
      
    