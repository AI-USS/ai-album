from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from .forms import ImageForm
from .models import Photographic, Tag


class HomePageView(TemplateView):
    template_name = "home.html"

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
        form = ImageForm(request.POST, request.FILES)
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
        form = ImageForm()

    return render(request, 'add.html', {'form': form})

class SearchPageView(TemplateView):
    template_name = "search.html"