import os
import chromadb
from chromadb.utils import embedding_functions
import time
from django.conf import settings 
import uuid


def init_chromadb(collection_name: str):
    """
    Inizializza il client ChromaDB e crea (o carica) la collection.
    """
    db_path = os.path.join(settings.BASE_DIR, "database", "chromadb_data")
    
    # Crea la directory se non esiste
    if not os.path.exists(db_path):
        os.makedirs(db_path)
    
    client = chromadb.PersistentClient(path=db_path)
    model = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
    collection = client.get_or_create_collection(name=collection_name, embedding_function=embedding_function)
    
    return collection

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
    print("<--------------------------------------->")
    print("<--------------------------------------->")
    print("<--------------------------------------->")
    print("<--------------------------------------->")
    print("<--------------------------------------->")

    file_id_string = str(document_pk) 
    where_filter = {"document_pk": file_id_string }
    deleted_ids = collection.delete(where=where_filter)
    
    if deleted_ids is None:
        deleted_ids = []
    
    return deleted_ids