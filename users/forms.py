from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        }),
        help_text='Required. Enter a valid email address.'
    )
    
    is_uploader = forms.BooleanField(
        required=False, 
        label='Can Upload & Process Documents (Uploader Role)'
    )
    is_searcher = forms.BooleanField(
        required=False, 
        label='Can Search & View Documents (Searcher Role)'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'is_uploader', 'is_searcher')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_uploader', 'is_searcher']:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        """
        Validazione personalizzata per assicurarsi che almeno un ruolo sia selezionato.
        """
        cleaned_data = super().clean()
        is_uploader = cleaned_data.get('is_uploader')
        is_searcher = cleaned_data.get('is_searcher')
        
        if not is_uploader and not is_searcher:
            raise ValidationError(
                "You must select at least one role (Uploader or Searcher) to register."
            )
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email').lower()
        
        if commit:
            user.save()
            profile = user.profile
            profile.is_uploader = self.cleaned_data.get('is_uploader')
            profile.is_searcher = self.cleaned_data.get('is_searcher')
            profile.save()
            
        return user