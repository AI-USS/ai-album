from django.forms import ModelForm
from .models import Photographic
from django import forms
import base64


class AddPhotoForm(ModelForm):
    awers = forms.ImageField()

    class Meta:
        model = Photographic
        fields = ["awers", "description"]