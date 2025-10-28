from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .models import Document
from .mixins import SearcherRequiredMixin, UploaderRequiredMixin 


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
    
class DocumentListView(SearcherRequiredMixin, ListView):
    # Dobbiamo importare 'Document' come modello
    model = Document
    
    # Il template che useremo per visualizzare la lista
    template_name = 'doc_manager/document_list.html'
    
    # Il nome della variabile nel contesto del template
    context_object_name = 'documents' 
    
    def get_queryset(self):
        # 1. Recupera la query di base (tutti i documenti, ordinati)
        queryset = super().get_queryset()
        
        # 2. Implementazione della logica di Ricerca
        search_query = self.request.GET.get('q') # Recupera il parametro di ricerca 'q' dall'URL
        if search_query:
            # Filtra i documenti dove il titolo contiene la query
            # (Usiamo __icontains per una ricerca case-insensitive)
            queryset = queryset.filter(title__icontains=search_query) 
        
        # 3. Restituisci il set di risultati (filtrato o completo)
        return queryset
    
class DocumentProcessView(UpdateView):
    model = Document 
    fields = ['is_processed', 'processing_output'] 
    template_name = 'doc_manager/document_process_form.html'
    success_url = reverse_lazy('document_list') 
    
    # Questo metodo garantisce che solo il proprietario del documento possa vederlo
    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        
        # Aggiungiamo un controllo per l'autenticazione E la proprietà
        if not self.request.user.is_authenticated or doc.uploader != self.request.user:
            # Se l'utente non è loggato O non è il proprietario, restituiamo un 404
            # Una soluzione più pulita userebbe un Mixin, ma questa è veloce
            # per un controllo sulla proprietà dell'oggetto.
            raise Http404("You are not authorized to process this document.")
            
        return doc

    def form_valid(self, form):
        # QUI si simula la logica di processamento (es. estrazione testo con Tesseract/PDFMiner)
        
        # Simulazione: se il flag è impostato a True, aggiungiamo un risultato
        if form.cleaned_data.get('is_processed') == True and not form.instance.processing_output:
            form.instance.processing_output = f"Document '{form.instance.title}' successfully processed by system."

        return super().form_valid(form)