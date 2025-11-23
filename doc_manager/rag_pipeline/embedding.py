import os
import chromadb
from chromadb.utils import embedding_functions
from django.conf import settings 
import uuid
from .config import get_collection_name, get_embedding_model


def init_chromadb(collection_name=None):
    """
    Inizializza il client ChromaDB e crea (o carica) la collection.
    """
    db_path = os.path.join(settings.BASE_DIR, "database", "chromadb_data")
    
    # Crea la directory se non esiste
    if not os.path.exists(db_path):
        os.makedirs(db_path)
    
    client = chromadb.PersistentClient(path=db_path)
    COLLECTION_NAME = get_collection_name()    
    MODEL_NAME = get_embedding_model()
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding_function)
        
    return collection


def clean_metadata(metadata):
    """
    Pulisce i metadata rimuovendo valori None e convertendo i tipi non supportati.
    """
    cleaned = {}
    
    for key, value in metadata.items():
        # Salta valori None
        if value is None:
            continue
            
        # Converti tutti i valori in tipi supportati
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, (list, dict)):
            # Converti liste e dizionari in stringhe
            cleaned[key] = str(value)
        else:
            # Converti altri tipi in stringa
            cleaned[key] = str(value)
    
    return cleaned


def add_chunks_to_db(collection, chunks, document_pk: int):
    """
    Aggiunge i chunk alla collection ChromaDB.
    """
    documents = [c["content"] for c in chunks]
    metadatas_with_pk = []
    doc_pk_str = str(document_pk) 
    
    for c in chunks:
        meta = c["metadata"].copy() 
        meta["document_pk"] = doc_pk_str
        meta = clean_metadata(meta)
        
        metadatas_with_pk.append(meta)

    ids = [f"{uuid.uuid4()}" for _ in chunks]

    try:
        collection.add(
            documents=documents, 
            metadatas=metadatas_with_pk,
            ids=ids
        )
    except chromadb.errors.IDAlreadyExistsError:
        collection.upsert(
            documents=documents, 
            metadatas=metadatas_with_pk,
            ids=ids
        )


def delete_document_embeddings(collection, document_pk: int): 
    file_id_string = str(document_pk) 
    where_filter = {"document_pk": file_id_string }
    deleted_ids = collection.delete(where=where_filter)
    
    if deleted_ids is None:
        deleted_ids = []
        
    return deleted_ids