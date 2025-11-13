from django import forms
from .models import Document
from django.core.exceptions import ValidationError

# Form per l'upload del documento con selezione del tipo
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'document_type']
        widgets = {
            'document_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    # Controllo di validità del titolo
    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        if Document.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError(
                f"Esiste già un documento con il titolo: '{title}'. Scegli un titolo diverso."
            )
        
        return title
    
    
# Form per rinominare un documento esistente
class DocumentRenameForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter new document title'
            })
        }
        labels = {
            'title': 'New Document Title'
        }
    
    def __init__(self, *args, **kwargs):
        # Salviamo l'ID del documento corrente per escluderlo dalla validazione
        self.document_id = kwargs.pop('document_id', None)
        super().__init__(*args, **kwargs)
    
    def clean_title(self):
        """
        Verifica che il nuovo titolo non sia già utilizzato.
        """
        title = self.cleaned_data.get('title')
        
        # Query per verificare duplicati, escludendo il documento corrente
        query = Document.objects.filter(title__iexact=title)
        if self.document_id:
            query = query.exclude(pk=self.document_id)
        
        if query.exists():
            raise ValidationError(
                f"Another document already has the title: '{title}'. Please choose a different name."
            )
        
        return title