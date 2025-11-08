from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django import forms
import os

from .models import Document
from .mixins import SearcherRequiredMixin, UploaderRequiredMixin 
from .tasks import index_document_rag, process_scanned_document
from .rag_pipeline.embedding import init_chromadb
from .rag_pipeline.search import run_queries
from itertools import groupby
from operator import itemgetter

COLLECTION_NAME = "docseek_collection"

class DocumentUploadForm(forms.ModelForm):
    """Form personalizzato per l'upload con selezione del tipo"""
    class Meta:
        model = Document
        fields = ['title', 'file', 'document_type']
        widgets = {
            'document_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

class DocumentCreateView(UploaderRequiredMixin, CreateView):
    model = Document 
    form_class = DocumentUploadForm
    template_name = 'doc_manager/document_form.html'
    success_url = reverse_lazy('document_list') 

    def form_valid(self, form):
        form.instance.uploader = self.request.user 
        form.instance.processing_state = 'pending'
        self.object = form.save()
        
        doc_type = form.cleaned_data.get('document_type')
        if doc_type == 'scanned':
            messages.info(
                self.request, 
                f"Scanned document '{self.object.title}' uploaded. It will require OCR processing."
            )
        else:
            messages.success(
                self.request, 
                f"Document '{self.object.title}' uploaded successfully. Ready for processing."
            )
        
        return redirect(reverse_lazy('document_process', kwargs={'pk': self.object.pk}))    

class DocumentListView(SearcherRequiredMixin, ListView):
    model = Document
    template_name = 'doc_manager/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        if self.request.user.profile.is_searcher:
            return Document.objects.filter(is_processed=True).order_by('-uploaded_at') 
        
        return Document.objects.filter(uploader=self.request.user).order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '').strip()
        context['rag_results_by_doc'] = None 
        context['search_query'] = search_query

        if self.request.user.profile.is_searcher and search_query:
            try:
                collection = init_chromadb(COLLECTION_NAME)
                rag_results = run_queries(collection, [search_query], n_results=5)
                
                if rag_results and rag_results[0].get('chunks'):
                    raw_chunks = rag_results[0]['chunks']
                    sorted_chunks = sorted(raw_chunks, key=itemgetter('document_title'))
                    
                    grouped_results = {}
                    for title, group in groupby(sorted_chunks, key=itemgetter('document_title')):
                        grouped_results[title] = list(group)
                    
                    context['rag_results_by_doc'] = grouped_results
                else:
                    context['rag_error'] = "Semantic search executed, but no relevant content was found."
                
            except Exception as e:
                context['rag_error'] = f"RAG search failed: {e}"
        
        return context
    
    
class DocumentProcessView(UpdateView):
    model = Document 
    fields = ['is_processed', 'processing_output'] 
    template_name = 'doc_manager/document_process_form.html'
    success_url = reverse_lazy('document_list') 
    
    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        
        if not self.request.user.is_authenticated or doc.uploader != self.request.user:
            raise Http404("You are not authorized to process this document.")
            
        return doc
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = self.object
        return context

    def form_valid(self, form):
        doc_instance = form.save(commit=False)
        
        if form.cleaned_data.get('is_processed') and not Document.objects.get(pk=doc_instance.pk).is_processed:
            
            if doc_instance.document_type == 'scanned':
                process_scanned_document.delay(doc_instance.pk)
                doc_instance.processing_state = 'ocr_queued'
                doc_instance.processing_output = "Document sent for OCR processing on GPU server."
                messages.info(
                    self.request, 
                    f"Scanned document '{doc_instance.title}' sent for OCR. This may take several minutes."
                )
            else:
                # Processamento normale per PDF nativi
                index_document_rag.delay(doc_instance.pk)
                doc_instance.processing_state = 'rag_processing'
                doc_instance.processing_output = "Indexing started in background."
                messages.info(
                    self.request, 
                    f"Processing of '{doc_instance.title}' started! Check 'Search & Results' later."
                )
            
            doc_instance.is_processed = False
        else:
            messages.success(self.request, f"Document '{doc_instance.title}' details updated.")
            
        doc_instance.save()
        return redirect(self.success_url)
    
class DocumentDeleteView(UploaderRequiredMixin, DeleteView):
    """View per eliminare documenti - solo l'uploader può eliminare i propri documenti"""
    model = Document
    template_name = 'doc_manager/document_confirm_delete.html'
    success_url = reverse_lazy('uploader_dashboard')
    
    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        
        if doc.uploader != self.request.user:
            raise Http404("You are not authorized to delete this document.")
    
        return doc
    
    def delete(self, request, *args, **kwargs):
        """
        Sovrascrive il metodo delete per:
        1. Eliminare i file fisici (originale e processato)
        2. Rimuovere i chunk da ChromaDB
        3. Eliminare il record dal database
        """
        self.object = self.get_object()
        document_title = self.object.title
        document_id = self.object.pk
        
        try:
            # Elimina i file fisici
            if self.object.file and os.path.isfile(self.object.file.path):
                os.remove(self.object.file.path)
                print(f"[DELETE] File originale eliminato: {self.object.file.path}")
            
            if self.object.processed_file and os.path.isfile(self.object.processed_file.path):
                os.remove(self.object.processed_file.path)
                print(f"[DELETE] File processato eliminato: {self.object.processed_file.path}")
            
            # Rimuovi i chunk da ChromaDB se il documento era processato
            if self.object.is_processed:
                try:
                    collection = init_chromadb(COLLECTION_NAME)
                    
                    # Cerca tutti i chunk con document_id corrispondente
                    results = collection.get(
                        where={"document_id": document_id}
                    )
                    
                    if results and results['ids']:
                        collection.delete(ids=results['ids'])
                        print(f"[DELETE] Eliminati {len(results['ids'])} chunk da ChromaDB per documento ID {document_id}")
                    else:
                        print(f"[DELETE] Nessun chunk trovato in ChromaDB per documento ID {document_id}")
                        
                except Exception as e:
                    print(f"[DELETE] Errore durante eliminazione chunk da ChromaDB: {e}")
            
            # Elimina il record dal database
            self.object.delete()
            
            messages.success(
                request, 
                f"Document '{document_title}' has been successfully deleted along with all associated data."
            )
            
        except Exception as e:
            messages.error(
                request, 
                f"Error deleting document '{document_title}': {str(e)}"
            )
            print(f"[DELETE] Errore critico durante eliminazione: {e}")
        
        return redirect(self.success_url)

class UploaderDashboardView(UploaderRequiredMixin, ListView):
    model = Document
    template_name = 'doc_manager/uploader_dashboard.html'
    context_object_name = 'pending_documents'

    def get_queryset(self):
        return Document.objects.filter(
            uploader=self.request.user,
            is_processed=False
        ).order_by('-uploaded_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_uploaded_count'] = Document.objects.filter(
            uploader=self.request.user
        ).count()
        
        context['processed_count'] = Document.objects.filter(
            uploader=self.request.user,
            is_processed=True
        ).count()
        
        # Aggiungi statistiche OCR
        context['ocr_processing_count'] = Document.objects.filter(
            uploader=self.request.user,
            document_type='scanned',
            processing_state__in=['ocr_queued', 'ocr_processing']
        ).count()
        
        # Aggiungi documenti processati
        context['processed_documents'] = Document.objects.filter(
            uploader=self.request.user,
            is_processed=True
        ).order_by('-uploaded_at')
        
        return context