from django import forms
from .models import Document
from django.core.exceptions import ValidationError

# Form per l'upload del documento con selezione del tipo
class DocumentUploadForm(forms.ModelForm):
    """Form personalizzato per l'upload con selezione del tipo"""
    class Meta:
        model = Document
        fields = ['title', 'file', 'document_type']
        widgets = {
            'document_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    # Controllo di validità del titolo
    def clean_title(self):
        """
        Controlla se esiste già un documento con lo stesso titolo 
        nel database.
        """
        title = self.cleaned_data.get('title')
        
        if Document.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError(
                f"Esiste già un documento con il titolo: '{title}'. Scegli un titolo diverso."
            )
        
        return title