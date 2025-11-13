from django.http import Http404, FileResponse, HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
import os
from django.contrib import messages

from .models import Document
from .mixins import SearcherRequiredMixin, UploaderRequiredMixin 
from .tasks import index_document_rag, process_scanned_document
from .rag_pipeline.embedding import init_chromadb, delete_document_embeddings, add_chunks_to_db
from .rag_pipeline.search import run_queries
from .forms import DocumentUploadForm, DocumentRenameForm
from itertools import groupby
from operator import itemgetter

COLLECTION_NAME = "docseek_collection"


# View per l'upload del documento
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


# View per la lista dei documenti
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
    

# View per il processamento del documento
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
    

# View per rinominare un documento
class DocumentRenameView(UploaderRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentRenameForm
    template_name = 'doc_manager/document_rename.html'
    success_url = reverse_lazy('uploader_dashboard')
    
    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        
        if doc.uploader != self.request.user:
            raise Http404("You are not authorized to rename this document.")
            
        return doc
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['document_id'] = self.object.pk
        return kwargs
    
    def form_valid(self, form):
        old_title = self.object.title
        response = super().form_valid(form)
        new_title = self.object.title
        
        messages.success(
            self.request,
            f'Document renamed successfully from "{old_title}" to "{new_title}".'
        )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['old_title'] = self.object.title
        return context


# View per l'eliminazione del documento
class DocumentDeleteView(DeleteView):
    model = Document
    template_name = 'doc_manager/document_confirm_delete.html'
    success_url = reverse_lazy('uploader_dashboard')
    
    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        
        if doc.uploader != self.request.user:
            raise Http404("You are not authorized to delete this document.")
            
        return doc
    
    def form_valid(self, form):
        self.object = self.get_object()
        document_id = self.object.pk  

        if self.object.file and os.path.isfile(self.object.file.path):
            os.remove(self.object.file.path)
            print(f"[DELETE] File originale eliminato: {self.object.file.path}")

        if self.object.processed_file and os.path.isfile(self.object.processed_file.path):
            os.remove(self.object.processed_file.path)
            print(f"[DELETE] File processato eliminato: {self.object.processed_file.path}")

        if self.object.is_processed:
            collection = init_chromadb(COLLECTION_NAME) 
            delete_document_embeddings(collection, document_id) 
            print(f"[DELETE] Embeddings RAG eliminati per Documento ID: {document_id}")
            
        self.object.delete()
        return redirect(self.success_url)


# View per la dashboard dell'uploader
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
        
        context['ocr_processing_count'] = Document.objects.filter(
            uploader=self.request.user,
            document_type='scanned',
            processing_state__in=['ocr_queued', 'ocr_processing']
        ).count()
        
        context['processed_documents'] = Document.objects.filter(
            uploader=self.request.user,
            is_processed=True
        ).order_by('-uploaded_at')
        
        return context


# View per visualizzare il documento PDF con PDF.js
class DocumentViewerView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'doc_manager/document_viewer.html'
    context_object_name = 'document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        page_number = self.request.GET.get('page', 1)
        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1
        
        context['initial_page'] = page_number
        
        document = self.get_object()
        if document.processed_file:
            context['pdf_url'] = document.processed_file.url
        else:
            context['pdf_url'] = document.file.url
        
        return context


@login_required
def serve_document_file(request, pk):
    """
    Serve il file PDF del documento.
    """
    document = get_object_or_404(Document, pk=pk)
    
    # Verifica permessi: l'uploader o un searcher possono visualizzare
    if not (document.uploader == request.user or request.user.profile.is_searcher):
        raise Http404("You don't have permission to view this document.")
    
    # Determina quale file servire
    if document.processed_file and os.path.exists(document.processed_file.path):
        file_path = document.processed_file.path
        filename = os.path.basename(document.processed_file.name)
    elif document.file and os.path.exists(document.file.path):
        file_path = document.file.path
        filename = os.path.basename(document.file.name)
    else:
        raise Http404("Document file not found.")
    
    # Serve il file
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    return response