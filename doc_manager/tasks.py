from celery import shared_task
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
import os
import requests
from .models import Document
from .rag_pipeline.processing import convert_pdf_to_doc, create_chunks, create_chunks_scannedpdf
from .rag_pipeline.embedding import init_chromadb, add_chunks_to_db

COLLECTION_NAME = "docseek_collection"
GPU_SERVER_URL = getattr(settings, 'GPU_SERVER_URL', 'http://localhost:8000')
OCR_TIMEOUT = getattr(settings, 'OCR_REQUEST_TIMEOUT', 300)

@shared_task
def process_scanned_document(document_pk):
    """
    Task che invia il documento scansionato al server GPU per OCR con DeepSeek-VL.
    """
    try:
        doc_instance = get_object_or_404(Document, pk=document_pk)
        doc_instance.processing_state = 'ocr_queued'
        doc_instance.save()
        
        print(f"[OCR] Invio documento {doc_instance.title} al server GPU...")
        
        file_path = doc_instance.file.path
        
        # Verifica che il file esista
        if not os.path.exists(file_path):
            print(f"[OCR] ERRORE: File non trovato: {file_path}")
            doc_instance.processing_state = 'ocr_failed'
            doc_instance.ocr_error = "File not found"
            doc_instance.save()
            return
        
        try:
            # Invio del file al server GPU
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
                data = {
                    'document_id': document_pk,
                    'title': doc_instance.title
                }
                
                print(f"[OCR] Connessione a {GPU_SERVER_URL}...")
                response = requests.post(
                    f'{GPU_SERVER_URL}/api/ocr/process',
                    files=files,
                    data=data,
                    timeout=OCR_TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('task_id')
                    
                    doc_instance.processing_state = 'ocr_processing'
                    doc_instance.processing_output = f"OCR avviato su GPU. Task ID: {task_id}"
                    doc_instance.save()
                    
                    print(f"[OCR] Task GPU creato con successo: {task_id}")
                    
                    check_ocr_status.apply_async(
                        args=[document_pk, task_id],
                        countdown=30  
                    )
                else:
                    raise Exception(f"GPU server returned status {response.status_code}: {response.text}")
                
        except requests.ConnectionError as e:
            error_msg = f"Impossibile connettersi al server GPU: {str(e)}"
            print(f"[OCR] ERRORE: {error_msg}")
            print(f"[OCR] Verifica che il server GPU sia attivo e raggiungibile")
            doc_instance.processing_state = 'ocr_failed'
            doc_instance.ocr_error = error_msg
            doc_instance.save()
            
        except requests.Timeout as e:
            error_msg = f"Timeout connessione al server GPU: {str(e)}"
            print(f"[OCR] ERRORE: {error_msg}")
            doc_instance.processing_state = 'ocr_failed'
            doc_instance.ocr_error = error_msg
            doc_instance.save()
                
    except Exception as e:
        print(f"[OCR] ERRORE CRITICO per documento ID {document_pk}: {e}")
        doc_instance = Document.objects.get(pk=document_pk)
        doc_instance.processing_state = 'ocr_failed'
        doc_instance.ocr_error = str(e)
        doc_instance.save()


@shared_task
def check_ocr_status(document_pk, task_id, retry_count=0):
    """
    Task che controlla periodicamente lo stato dell'OCR sul server GPU.
    """
    max_retries = 60 
    
    try:
        doc_instance = get_object_or_404(Document, pk=document_pk)
        
        print(f"[OCR] Controllo stato task {task_id} (tentativo {retry_count + 1}/{max_retries})...")
        
        response = requests.get(
            f'{GPU_SERVER_URL}/api/ocr/status/{task_id}',
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            progress = result.get('progress', 0)
            
            print(f"[OCR] Status: {status}, Progress: {progress}%")
            
            if status == 'completed':
                ocr_text = result.get('text', '')
                char_count = result.get('char_count', len(ocr_text))
                page_count = result.get('page_count', 0)
                
                doc_instance.ocr_text = ocr_text
                doc_instance.processing_state = 'ocr_completed'
                doc_instance.ocr_completed_at = timezone.now()
                doc_instance.processing_output = f"OCR completato. Estratti {char_count} caratteri da {page_count} pagine."
                doc_instance.save()
                
                print(f"[OCR] ✓ OCR completato per {doc_instance.title}")
                print(f"[OCR] Avvio indicizzazione RAG...")
                
                index_document_rag.delay(document_pk)
                
            elif status == 'failed':
                error = result.get('error', 'Unknown error')
                doc_instance.processing_state = 'ocr_failed'
                doc_instance.ocr_error = error
                doc_instance.save()
                print(f"[OCR] ✗ OCR fallito per {doc_instance.title}: {error}")
                
            elif status in ['pending', 'queued', 'processing']:
                doc_instance.processing_output = f"OCR in corso... Progresso: {progress}%"
                doc_instance.save()
                
                if retry_count < max_retries:
                    check_ocr_status.apply_async(
                        args=[document_pk, task_id, retry_count + 1],
                        countdown=60
                    )
                else:
                    doc_instance.processing_state = 'ocr_failed'
                    doc_instance.ocr_error = "Timeout: OCR non completato dopo 1 ora"
                    doc_instance.save()
                    print(f"[OCR] ✗ Timeout per {doc_instance.title}")
            else:
                print(f"[OCR] Status sconosciuto: {status}")
        else:
            print(f"[OCR] Errore response: {response.status_code}")
            if retry_count < max_retries:
                check_ocr_status.apply_async(
                    args=[document_pk, task_id, retry_count + 1],
                    countdown=120 
                )
                
    except requests.RequestException as e:
        print(f"[OCR] Errore connessione durante status check: {e}")
        if retry_count < max_retries:
            check_ocr_status.apply_async(
                args=[document_pk, task_id, retry_count + 1],
                countdown=120
            )
    except Exception as e:
        print(f"[OCR] ERRORE durante status check per ID {document_pk}: {e}")


@shared_task
def index_document_rag(document_pk):
    """
    Task asincrono per l'indicizzazione RAG di un documento.
    Gestisce sia PDF nativi che documenti con OCR completato.
    """
    try:
        doc_instance = get_object_or_404(Document, pk=document_pk)
        
        print(f"[RAG] Inizio indicizzazione per: {doc_instance.title}")
        
        if doc_instance.document_type == 'scanned':
            if not doc_instance.ocr_text:
                print(f"[RAG] ERRORE: Nessun testo OCR disponibile per documento {document_pk}")
                doc_instance.processing_state = 'failed'
                doc_instance.processing_output = "Errore: testo OCR non disponibile"
                doc_instance.save()
                return
            
            print(f"[RAG] Creazione chunks da testo OCR...")
            doc_instance.processing_state = 'rag_processing'
            doc_instance.save()
            
            chunks = create_chunks_scannedpdf(
                doc_instance.ocr_text, 
                doc_instance.title
            )
            
        else:
            file_path = doc_instance.file.path
            
            if not os.path.exists(file_path):
                print(f"[RAG] ERRORE: File non trovato per documento ID {document_pk}")
                doc_instance.processing_state = 'failed'
                doc_instance.processing_output = "Errore: file non trovato"
                doc_instance.save()
                return
                
            print(f"[RAG] Elaborazione PDF nativo...")
            doc_instance.processing_state = 'rag_processing'
            doc_instance.save()
            
            # Conversione PDF -> Docling
            document = convert_pdf_to_doc(file_path)
            chunks = create_chunks(document)
        
        # Aggiungi metadata comuni
        for c in chunks:
            c["metadata"]["source_title"] = doc_instance.title
            c["metadata"]["document_id"] = document_pk
            c["metadata"]["uploader"] = doc_instance.uploader.username
            c["metadata"]["document_type"] = doc_instance.document_type

        # Setup del DB e indicizzazione
        print(f"[RAG] Indicizzazione {len(chunks)} chunks in ChromaDB...")
        collection = init_chromadb(COLLECTION_NAME)
        add_chunks_to_db(collection, chunks, document_pk)

        # Aggiorna stato documento
        doc_instance.is_processed = True
        doc_instance.processing_state = 'completed'
        doc_instance.processing_output = f"✓ Indicizzati {len(chunks)} chunks in ChromaDB. Documento pronto per ricerca semantica."
        doc_instance.save()
        
        print(f"[RAG] ✓ Indicizzazione completata per {doc_instance.title}")

    except Exception as e:
        print(f"[RAG] ERRORE CRITICO durante indicizzazione per ID {document_pk}: {e}")
        import traceback
        traceback.print_exc()
        
        doc_instance = Document.objects.get(pk=document_pk)
        doc_instance.processing_state = 'failed'
        doc_instance.processing_output = f"Errore durante indicizzazione: {str(e)}"
        doc_instance.save()
