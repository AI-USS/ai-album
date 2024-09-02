from django import forms

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
            'placeholder': 'Wpisz tagi oddzielone przecinkami, np. \'wakacje, rodzina\'',
            'id':'tags'
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
    
    
