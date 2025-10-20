from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
import chromadb
from chromadb.utils import embedding_functions
import time

INPUT_FORMAT_PDF = "pdf"
pdf_filename = "data/test_document2.pdf" 

def flush_text_buffer(buffer, page_num, all_chunks_list):
    """
    Unisce il testo nel buffer e lo aggiunge come un unico chunk.
    """
    if buffer:
        content = "\n".join(buffer)
        all_chunks_list.append({
            "content": content,
            "metadata": {"page": page_num, "type": "text"}
        })
    buffer.clear()

def convert_table_to_markdown(table_data, page_num: int) -> str:
    """
    Converte i dati della tabella Docling (usando .grid) in una stringa Markdown.
    (Rimosso il type hint 'TableData' dall'argomento 'table_data')
    """
    grid = table_data.grid
    if not grid:
        return f"Tabella vuota a pagina {page_num}"
    
    markdown = f"Tabella a pagina {page_num}:\n"
    
    # Header
    markdown += "| " + " | ".join(cell.text for cell in grid[0]) + " |\n"
    # Separatore
    markdown += "| " + " | ".join(["---"] * len(grid[0])) + " |\n"
    # Righe del corpo
    for row in grid[1:]:
        markdown += "| " + " | ".join(cell.text for cell in row) + " |\n"
        
    return markdown

def create_logical_chunks(doc):
    """
    Crea chunk intelligenti seguendo la struttura logica 
    di document.body.children.
    (Rimosso il type hint 'DoclingDocument' dall'argomento 'doc')
    """
    all_chunks = []
    text_buffer = []
    current_page = 1  # Fallback per la pagina
    
    # Mappiamo i riferimenti (cref) agli oggetti reali per un accesso facile
    item_map = {}
    for item in doc.texts + doc.tables + doc.pictures:
        item_map[item.self_ref] = item
        
    # Iteriamo sull'ordine logico del documento
    for ref_item in doc.body.children:
        cref = ref_item.cref
        if cref not in item_map:
            continue
            
        item = item_map[cref]
        
        # Aggiorniamo il numero di pagina corrente
        if item.prov:
            current_page = item.prov[0].page_no
        
        # Usiamo .name per ottenere la stringa, es. 'TEXT', 'TABLE'
        item_type = item.label.name
        
        # --- Logica di Chunking ---
        
        if item_type in ['TEXT', 'SECTION_HEADER', 'LIST']:
            # 1. È testo. Lo aggiungiamo al buffer.
            text_buffer.append(item.text)
            
        elif item_type == 'TABLE':
            # 2. È una tabella.
            # Prima, salviamo tutto il testo che la precede.
            flush_text_buffer(text_buffer, current_page, all_chunks)
            
            # Poi, creiamo il chunk per la tabella
            table_md = convert_table_to_markdown(item.data, current_page)
            all_chunks.append({
                "content": table_md,
                "metadata": {"page": current_page, "type": "table"}
            })
            
        elif item_type == 'PICTURE':
            # 3. È un'immagine.
            flush_text_buffer(text_buffer, current_page, all_chunks)
            
            desc = "Immagine rilevata (nessuna didascalia trovata)"
            
            # item.captions è una LISTA DI RefItem
            if item.captions:
                caption_texts = []
                for ref in item.captions:
                    # 'ref' è un RefItem. Usiamo il suo 'cref' 
                    # per trovare l'oggetto reale nella item_map.
                    if ref.cref in item_map:
                        caption_item = item_map[ref.cref]
                        # Ora prendiamo il .text dall'oggetto reale
                        caption_texts.append(caption_item.text) 
                
                if caption_texts:
                    desc = "\n".join(caption_texts)

            img_summary = f"Riferimento a immagine (Pagina {current_page}). Didascalia: '{desc}'"
            all_chunks.append({
                "content": img_summary,
                "metadata": {"page": current_page, "type": "image"}
            })
            
    # Fine del ciclo. Svuotiamo il buffer un'ultima volta
    flush_text_buffer(text_buffer, current_page, all_chunks)
    
    return all_chunks


# --- MAIN ---

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,        # Riconoscimento e ricostruzione delle tabelle
    generate_picture_images=True    # Estrazione delle immagini incorporate nel PDF
)

pdf_format_options = PdfFormatOption(pipeline_options=pipeline_options)
doc_converter = DocumentConverter(
    format_options={INPUT_FORMAT_PDF: pdf_format_options}
)

print(f"Inizio analisi strutturata di: {pdf_filename}")

conv_res = doc_converter.convert(pdf_filename)
document = conv_res.document

try:
    intelligent_chunks = create_logical_chunks(document)

    print(f"--- Creati {len(intelligent_chunks)} chunk logici ---")

    for i, chunk in enumerate(intelligent_chunks):
        print(f"\n--- Chunk {i+1} (Tipo: {chunk['metadata']['type']}, Pagina: {chunk['metadata']['page']}) ---")
        print(chunk['content'])

except NameError as e:
    if 'document' in str(e):
        print("Errore: assicurati di avere l'oggetto 'document' caricato dal tuo codice precedente.")
    else:
        raise e
    
print(f"Ho {len(intelligent_chunks)} chunk pronti per l'indicizzazione.")

# --- 1. Setup del client di ChromaDB ---
# Salverà i dati su disco nella cartella 'db_tesi_docling'
client = chromadb.PersistentClient(path="./db_tesi_docling")

# --- 2. Setup del modello di Embedding ---
# Usiamo un modello multilingua (italiano/inglese) 
# molto valido e leggero.
model_name = "paraphrase-multilingual-MiniLM-L12-v2"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=model_name
)

# --- 3. Creazione (o caricamento) della Collection ---
collection_name = "docling_paper"
collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_function
)
print(f"Collection '{collection_name}' pronta.")

# --- 4. Preparazione dei dati per ChromaDB ---
documents_to_add = [chunk["content"] for chunk in intelligent_chunks]
metadatas_to_add = [chunk["metadata"] for chunk in intelligent_chunks]

# Creiamo ID unici per ogni chunk
ids_to_add = [f"chunk_{i}_page_{chunk['metadata']['page']}" for i, chunk in enumerate(intelligent_chunks)]

# --- 5. Indicizzazione (Aggiunta dei dati) ---
print(f"Inizio l'indicizzazione di {len(documents_to_add)} chunk...")
print("Questo potrebbe richiedere qualche minuto, specialmente la prima volta...")

start_time = time.time()

# Aggiungiamo i dati alla collection. 
# ChromaDB si occuperà di:
# 1. Prendere ogni 'document' (il testo del chunk)
# 2. Passarlo a 'embedding_function' (sentence-transformer)
# 3. Salvare il vettore risultante insieme ai 'metadatas' e 'ids'
try:
    collection.add(
        documents=documents_to_add,
        metadatas=metadatas_to_add,
        ids=ids_to_add
    )
except chromadb.errors.IDAlreadyExistsError:
    print("\nAttenzione: Questi ID esistono già nel database.")
    print("Uso 'upsert' per aggiornare i dati (se sono cambiati).")
    collection.upsert(
        documents=documents_to_add,
        metadatas=metadatas_to_add,
        ids=ids_to_add
    )

end_time = time.time()
print("\n--- Indicizzazione Completata! ---")
print(f"Tempo impiegato: {end_time - start_time:.2f} secondi.")
print(f"Numero totale di chunk nel database: {collection.count()}")

# --- 2. Le Domande (come lista) ---
queries = [
    "Dove si parla di Ecosystem?",
    "dove è la tabella?"
]

# --- 3. Eseguire le Query ---
print(f"\nEseguo {len(queries)} query in batch...")

# Chiediamo i 3 risultati più pertinenti PER OGNI query
results = collection.query(
    query_texts=queries,
    n_results=3 
)

# --- 4. Stampare i Risultati ---
print("\n--- Risultati della Ricerca Trovati ---")

if not results['documents']:
    print("Nessun risultato trovato.")
else:
    # Ora dobbiamo iterare su ogni query e i suoi risultati
    
    # zip unisce la nostra lista di query con le liste di risultati
    # (es. queries[0] con results['documents'][0], ecc.)
    for q_idx, query in enumerate(queries):
        print(f"\n==============================================")
        print(f"RISULTATI PER LA QUERY: '{query}'")
        print(f"==============================================")
        
        # Estraiamo i risultati per QUESTA query (q_idx)
        docs = results['documents'][q_idx]
        metas = results['metadatas'][q_idx]
        dists = results['distances'][q_idx]
        
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
            print(f"\n--- Risultato {i+1} (Distanza: {dist:.4f}) ---")
            print(f"   Pagina: {meta.get('page', 'N/A')}")
            print(f"   Tipo:   {meta.get('type', 'N/A')}")
            print("\n   Contenuto:")
            for line in doc.strip().split('\n'):
                print(f"     {line}")
