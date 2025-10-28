from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile # Importiamo il nostro modello Profile

class UserRegistrationForm(UserCreationForm):
    # Campi per il modello Profile
    is_uploader = forms.BooleanField(required=False, label='Can Upload & Process Documents (Uploader Role)')
    is_searcher = forms.BooleanField(required=False, label='Can Search & View Documents (Searcher Role)')

    class Meta(UserCreationForm.Meta):
        # Aggiungiamo i campi email e i campi per il profilo
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'is_uploader', 'is_searcher')

    def save(self, commit=True):
        # 1. Salviamo l'utente base (username e password)
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
            
            # 2. Creiamo il profilo e assegniamo i ruoli
            profile = user.profile
            profile.is_uploader = self.cleaned_data.get('is_uploader')
            profile.is_searcher = self.cleaned_data.get('is_searcher')
            profile.save()
            
        return user