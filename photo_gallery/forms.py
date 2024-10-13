from django import forms
from .models import Photographic

class AddPhotoForm(forms.Form):
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'id':'awers',
            'accept':'image/*',
        })
    )

    description = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-400 focus:border-teal-400 sm:text-sm',
            'placeholder': 'Dodaj krótki opis zdjęcia',
            'id':'description',
            'rows':'3'
        }),
        required=False

    )

    tags = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-400 focus:border-teal-400 sm:text-sm',
            'placeholder': 'Wpisz tagi zaczynając od # i zatwierdź spacją, np. \'#wakacje #rodzina \'',
            'class': 'hidden',
            'id':'djtags'
        }),
        required=False

    )

    additional_data = forms.CharField(
        widget=forms.TextInput(attrs={
            'id':'additional_data',
            'class': 'hidden'
        }),
        required=False
    )
    
    
class ModelLearnForm(forms.Form):
    class Meta:
        widgets = {"any_field": forms.HiddenInput()}



class EditPhotoForm(forms.ModelForm):

    rewers_image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'id':'rewers',
            'accept':'image/*',
        }),
        required=False
    )

    description = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-400 focus:border-teal-400 sm:text-sm',
            'placeholder': 'Dodaj krótki opis zdjęcia',
            'id':'description',
            'rows':'3'
        }),
        required=False

    )

    djtags = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-teal-400 focus:border-teal-400 sm:text-sm',
            'placeholder': 'Wpisz tagi oddzielone przecinkami, np. \'wakacje, rodzina\'',
            'class': 'hidden',
            'id':'djtags'
        }),
        required=False

    )

    additional_data = forms.CharField(
        widget=forms.TextInput(attrs={
            'id':'additional_data',
            'class': 'hidden'
        }),
        required=False
    )



    class Meta:
        model = Photographic
        fields = (
            # "image",
            "rewers_image",
            "description",
            "djtags",
        )