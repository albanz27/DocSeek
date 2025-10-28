from celery import shared_task
from django.shortcuts import get_object_or_404
from django.conf import settings
import os

# Importiamo il modello Document e le funzioni RAG
from .models import Document
from .rag_pipeline.processing import convert_pdf_to_doc, create_chunks
from .rag_pipeline.embedding import init_chromadb, add_chunks_to_db

COLLECTION_NAME = "docseek_collection" 

@shared_task
def index_document_rag(document_pk):
    """
    Task asincrono per l'indicizzazione RAG di un documento.
    """
    try:
        # 1. Recupera l'oggetto Document
        doc_instance = get_object_or_404(Document, pk=document_pk)
        
        # 2. Verifica se il file esiste (il percorso completo sul disco)
        # file_path = os.path.join(settings.MEDIA_ROOT, doc_instance.file.name)
        # Usiamo doc_instance.file.path che gestisce il percorso assoluto
        file_path = doc_instance.file.path

        if not os.path.exists(file_path):
            # Gestione errore: File non trovato
            print(f"ERRORE: File non trovato per il documento ID {document_pk} al percorso: {file_path}")
            return
            
        # 3. Pipeline RAG: Conversione, Chunking, e Indicizzazione
        print(f"Inizio il processamento asincrono di: {doc_instance.title}")

        # Conversione PDF -> Docling
        document = convert_pdf_to_doc(file_path)

        # Creazione dei chunk logici
        chunks = create_chunks(document)
        
        # Aggiungi metadata per la sorgente
        for c in chunks:
            c["metadata"]["source_title"] = doc_instance.title
            c["metadata"]["document_id"] = document_pk
            c["metadata"]["uploader"] = doc_instance.uploader.username

        # Setup del DB e indicizzazione
        collection = init_chromadb(COLLECTION_NAME)
        add_chunks_to_db(collection, chunks)

        # 4. Aggiorna lo stato in Django (marco come processato e aggiungo l'output simulato)
        doc_instance.is_processed = True
        doc_instance.processing_output = f"Successfully indexed {len(chunks)} chunks into ChromaDB."
        doc_instance.save()
        
        print(f"Indicizzazione completata per {doc_instance.title}.")

    except Exception as e:
        print(f"Errore critico durante il processamento RAG per ID {document_pk}: {e}")
        # Qui potresti salvare un messaggio d'errore sul Document