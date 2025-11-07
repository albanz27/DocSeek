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

def add_chunks_to_db(collection, chunks):
    """
    Aggiunge i chunk alla collection ChromaDB.
    """
    documents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"{uuid.uuid4()}" for _ in chunks]

    print(f"Inizio l'indicizzazione di {len(documents)} chunk...")
    start = time.time()

    try:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
    except chromadb.errors.IDAlreadyExistsError:
        print("ID già esistenti. Eseguo upsert...")
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)

    elapsed = time.time() - start
    print(f"Indicizzazione completata in {elapsed:.2f}s. Totale chunk nel DB: {collection.count()}")