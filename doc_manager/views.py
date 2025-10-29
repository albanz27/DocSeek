from django.http import Http404
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models import Document
from .mixins import SearcherRequiredMixin, UploaderRequiredMixin 
from .tasks import index_document_rag
from .rag_pipeline.embedding import init_chromadb
from .rag_pipeline.search import run_queries
from itertools import groupby
from operator import itemgetter

COLLECTION_NAME = "docseek_collection" 

class DocumentCreateView(UploaderRequiredMixin, CreateView):
    model = Document 
    fields = ['title', 'file'] 
    template_name = 'doc_manager/document_form.html'
    success_url = reverse_lazy('document_list') 

    def form_valid(self, form):
        form.instance.uploader = self.request.user 
        self.object = form.save()
        messages.success(self.request, f"Document '{self.object.title}' uploaded successfully. Ready for processing.")
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
                    context['rag_error'] = "Semantic search executed, but no relevant content was found in documents."
                
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
    

    def form_valid(self, form):
        doc_instance = form.save(commit=False)
        
        if form.cleaned_data.get('is_processed') and not Document.objects.get(pk=doc_instance.pk).is_processed:
            
            index_document_rag.delay(doc_instance.pk) 
            
            doc_instance.is_processed = False 
            doc_instance.processing_output = "Indexing started in background. Please check the list later."

            messages.info(self.request, f"Processing of '{doc_instance.title}' started! This may take a minute. Check 'Search & Results' later.")
        
        else:
            messages.success(self.request, f"Document '{doc_instance.title}' details updated.")
            
        return super().form_valid(form)
    
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
        context['processed_count'] = Document.objects.filter(
            uploader=self.request.user,
            is_processed=True
        ).count()
        return context