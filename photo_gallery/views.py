from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from .models import Photographic, Tag, Person, LearningPhotoFace, FaceEncoding
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import AddPhotoForm, ModelLearnForm
from collections import Counter
import face_recognition
from PIL import Image
import pickle
import json
import io
import base64


def home(request):
    from base64 import b64encode
    images = Photographic.objects.all().order_by('-id')[:12]
    for image in images:
        image.awers = b64encode(image.awers).decode('utf-8')
        
    return render(request, 'home.html', {'images': images})



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
            print(type(additional))
            
            print(file.image.format)

            # Save the image as a binary blob
            image_model = Photographic.objects.create(
                                    description=description,
                                    awers=image_data,
                                    format=file.image.format,
                                    width=file.image.size[0],
                                    height=file.image.size[1]
                                       )

            tagsORM, created = Tag.objects.get_or_create(keyword=tags)
            image_model.tags.add(tagsORM)
            image_model.save()
            print(30 * "-")
            print(additional)
            print(30 * "-")

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
    