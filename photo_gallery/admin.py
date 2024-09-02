from django.contrib import admin
from .models import Photographic
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
        "description",
        "width",
        "height",
    )


admin.site.register(Photographic, PhotographicAdmin)
