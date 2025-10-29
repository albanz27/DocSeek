from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile 

class UserRegistrationForm(UserCreationForm):
    is_uploader = forms.BooleanField(required=False, label='Can Upload & Process Documents (Uploader Role)')
    is_searcher = forms.BooleanField(required=False, label='Can Search & View Documents (Searcher Role)')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'is_uploader', 'is_searcher')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aggiunge la classe form-control a tutti i campi
        for field_name, field in self.fields.items():
            if field_name not in ['is_uploader', 'is_searcher']:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
            
            profile = user.profile
            profile.is_uploader = self.cleaned_data.get('is_uploader')
            profile.is_searcher = self.cleaned_data.get('is_searcher')
            profile.save()
            
        return user