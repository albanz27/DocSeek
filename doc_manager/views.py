from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.views.generic import ListView
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