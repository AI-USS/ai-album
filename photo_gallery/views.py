from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Photographic
from .forms import AddPhotoForm
import face_recognition
import json
import base64


class HomePageView(ListView):
    model = Photographic
    template_name = "home.html"


def convert_image_file_to_binary(file):
    binary_image = base64.b64encode(file.read())
    binary_image = base64.b64decode(binary_image)
    return binary_image

def upload_photo(request):
    if request.method == "POST":
        form = AddPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            photo = request.FILES["awers"]
            form.width = photo.image.width
            form.height = photo.image.height
            form.awers = convert_image_file_to_binary(photo)
            form.save()
            return HttpResponseRedirect("/")
    else:
        form = AddPhotoForm()
    return render(request, "add.html", {"form": form})

class SearchPageView(TemplateView):
    template_name = "search.html"


@csrf_exempt
def recognize_face_at_photo(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        photo = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(photo)
        return JsonResponse({"coords": face_locations})
    
    return JsonResponse({}, status=400)
