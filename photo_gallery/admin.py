from django.contrib import admin
from .models import Photographic, Tag, Person, LearningPhotoFace, PhotoVersion, FaceEncoding
from django.db import models
from django import forms
from .forms import AddPhotoForm

class PhotographicAdmin(admin.ModelAdmin):
    # formfield_overrides = {
    #     models.BinaryField: {"form_class": forms.ImageField}
    # }
    # form= AddPhotoForm
    exclude = ["awers"]
    readonly_fields = ("admin_awers_image_tag",)
    list_display = (
        "id",
        "description",
        "width",
        "height",
    )

class LearningPhotoFaceAdmin(admin.ModelAdmin):
    exclude = ["face"]
    readonly_fields = ("admin_awers_image_tag",)
    list_display = (
        "personid",
        "photographicid",
        "coordinates",
    )

admin.site.register(Photographic, PhotographicAdmin)
admin.site.register(Tag)
admin.site.register(Person)
admin.site.register(LearningPhotoFace, LearningPhotoFaceAdmin)
admin.site.register(PhotoVersion)
admin.site.register(FaceEncoding)