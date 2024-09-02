from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from .models import Photographic, Tag
from django.views.generic.list import ListView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import AddPhotoForm
import face_recognition
import json
import base64

def home(request):
    from base64 import b64encode
    images = Photographic.objects.all().order_by('-id')[:12]
    for image in images:
        image.awers = b64encode(image.awers).decode('utf-8')
        
    return render(request, 'home.html', {'images': images})


class AddPageView(TemplateView):
    template_name = "add.html"

def upload_image(request):
    if request.method == 'POST':
        form = AddPhotoForm(request.POST, request.FILES)
        if form.is_valid():

            file = form.cleaned_data['image']
            description = form.cleaned_data['description']
            tags = form.cleaned_data['tags']
            additional = form.cleaned_data['additional_data']

            image_data = file.read()

            print(file.image.format)

            # Save the image as a binary blob
            image_model = Photographic.objects.create(
                                    description=description,
                                    awers=image_data,
                                    format=file.image.format,
                                    width=file.image.size[0],
                                    height=file.image.size[1]
                                       )
            # image_model.save()
            # tags=set(tags.split(','))
            tagsORM, created = Tag.objects.get_or_create(keyword=tags)
            image_model.tags.add(tagsORM)
            image_model.save()

            return redirect('/')
    else:
        form = AddPhotoForm()

    return render(request, 'add.html', {'form': form})


@csrf_exempt
def recognize_face_at_photo(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        photo = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(photo)
        return JsonResponse({"coords": face_locations})
    
    return JsonResponse({}, status=400)

class SearchPageView(TemplateView):
    template_name = "search.html"
