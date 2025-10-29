from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect

from .models import Document
from .mixins import SearcherRequiredMixin, UploaderRequiredMixin 
from .tasks import index_document_rag
from .rag_pipeline.embedding import init_chromadb
from .rag_pipeline.search import run_queries

COLLECTION_NAME = "docseek_collection" # Deve corrispondere al nome nel task.py

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
        self.object = form.save()
        return redirect(reverse_lazy('document_process', kwargs={'pk': self.object.pk}))    

class DocumentListView(SearcherRequiredMixin, ListView):
    model = Document
    template_name = 'doc_manager/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        # Per il listato, i Searcher vedono solo i documenti processati.
        if self.request.user.profile.is_searcher:
            # Se è un Searcher, vediamo solo i processati (per la ricerca RAG)
            return Document.objects.filter(is_processed=True).order_by('-uploaded_at') 
        
        # Gli Uploader vedono tutti i loro documenti (per processarli)
        # Questa linea si esegue solo se NON sono Searcher. E se sono Superutente?
        return Document.objects.filter(uploader=self.request.user).order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '').strip()
        context['rag_results'] = None

        if self.request.user.profile.is_searcher and search_query:
            try:
                collection = init_chromadb(COLLECTION_NAME)
                # Esegui la query RAG, essa ritorna una lista di risultati
                rag_results = run_queries(collection, [search_query], n_results=3) 
                
                # Passa i risultati RAG al template
                context['rag_results'] = rag_results[0]['chunks'] # Solo i chunk del primo risultato
                
            except Exception as e:
                context['rag_error'] = f"Error during RAG search: {e}"
        
        return context
    
    
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
        # Salviamo l'istanza del documento senza commettere sul DB per ora
        doc_instance = form.save(commit=False)
        
        # Verifichiamo se l'utente ha spuntato "is_processed" 
        # e se il documento non era ancora stato processato (per evitare duplicati)
        if form.cleaned_data.get('is_processed') and not Document.objects.get(pk=doc_instance.pk).is_processed:
            
            # 1. Chiamata al task Celery: il processamento avviene in background
            index_document_rag.delay(doc_instance.pk) # <-- CHIAMATA ASINCRONA
            
            # 2. Aggiorniamo subito lo stato e l'output per feedback immediato
            doc_instance.is_processed = False # Resettiamo temporaneamente finché Celery non finisce
            doc_instance.processing_output = "Indexing started in background. Please check the list later."
            
        # Salviamo l'istanza (con lo stato di 'Indexing started...')
        return super().form_valid(form)