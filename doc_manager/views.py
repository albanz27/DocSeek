from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Document
from .mixins import UploaderRequiredMixin 


class DocumentCreateView(UploaderRequiredMixin, CreateView):
    # Dobbiamo importare 'Document' come modello
    model = Document 
    
    # I campi che l'utente deve compilare
    fields = ['title', 'file'] 
    
    # Il template che useremo per mostrare il form
    template_name = 'doc_manager/document_form.html'
    
    # URL di reindirizzamento dopo l'upload (la lista documenti che faremo dopo)
    success_url = reverse_lazy('document_list') 

    def form_valid(self, form):
        # PRIMA di salvare, aggiungiamo l'utente loggato come 'uploader'
        form.instance.uploader = self.request.user 
        return super().form_valid(form)