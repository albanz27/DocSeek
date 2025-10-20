from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
import chromadb
from chromadb.utils import embedding_functions
import time


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
    Converte i dati della tabella Docling in una stringa Markdown.
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

def create_chunks(doc):
    all_chunks = []
    text_buffer = []
    current_page = 1 
    
    # Costruzione della mappa dei riferimenti (item_map)
    item_map = {}
    for item in doc.texts + doc.tables + doc.pictures:
        item_map[item.self_ref] = item
        
    # Iterazione sull'ordine logico del documento
    for ref_item in doc.body.children:
        cref = ref_item.cref
        if cref not in item_map:
            continue
            
        item = item_map[cref]
        
        # Aggiornamento del numero di pagina
        if item.prov:
            current_page = item.prov[0].page_no
        
        # Determinazione del tipo di elemento
        item_type = item.label.name
        
        if item_type in ['TEXT', 'SECTION_HEADER', 'LIST']:
            text_buffer.append(item.text)
            
        elif item_type == 'TABLE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            
            table_md = convert_table_to_markdown(item.data, current_page)
            all_chunks.append({
                "content": table_md,
                "metadata": {"page": current_page, "type": "table"}
            })
            
        elif item_type == 'PICTURE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            
            desc = "Immagine rilevata (nessuna didascalia trovata)"
            
            if item.captions:
                caption_texts = []
                for ref in item.captions:
                    if ref.cref in item_map:
                        caption_item = item_map[ref.cref]
                        caption_texts.append(caption_item.text) 
                
                if caption_texts:
                    desc = "\n".join(caption_texts)

            img_summary = f"Riferimento a immagine (Pagina {current_page}). Didascalia: '{desc}'"
            all_chunks.append({
                "content": img_summary,
                "metadata": {"page": current_page, "type": "image"}
            })
            
    # Svuotamento finale del buffer di testo
    flush_text_buffer(text_buffer, current_page, all_chunks)
    
    return all_chunks


# --- MAIN ---
INPUT_FORMAT_PDF = "pdf"
PDF_FILENAME = "data/test_document2.pdf" 

pipeline_options = PdfPipelineOptions(
    do_table_structure=True,        # Riconoscimento e ricostruzione delle tabelle
    generate_picture_images=True    # Estrazione delle immagini incorporate nel PDF
)

pdf_format_options = PdfFormatOption(pipeline_options=pipeline_options)
doc_converter = DocumentConverter(
    format_options={INPUT_FORMAT_PDF: pdf_format_options}
)

print(f"Inizio analisi strutturata di: {PDF_FILENAME}")

conv_res = doc_converter.convert(PDF_FILENAME)
document = conv_res.document

try:
    intelligent_chunks = create_chunks(document)

    print(f"--- Creati {len(intelligent_chunks)} chunk logici ---")

    for i, chunk in enumerate(intelligent_chunks):
        print(f"\n--- Chunk {i+1} (Tipo: {chunk['metadata']['type']}, Pagina: {chunk['metadata']['page']}) ---")
        print(chunk['content'])

except NameError as e:
    if 'document' in str(e):
        print("Errore: assicurati di avere l'oggetto 'document' caricato correttamente.")
    else:
        raise e
    
print(f"Ho {len(intelligent_chunks)} chunk pronti per l'indicizzazione.")

# --- Setup del client di ChromaDB con salvataggio dei dati sul disco ---
client = chromadb.PersistentClient(path="./database")

# --- Setup del modello di Embedding ---
model_name = "paraphrase-multilingual-MiniLM-L12-v2"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=model_name
)

# --- Creazione della Collection ---
collection_name = "docling_paper"
collection = client.get_or_create_collection(
    name=collection_name,
    embedding_function=embedding_function
)
print(f"Collection '{collection_name}' pronta.")

# --- Preparazione dei dati per ChromaDB ---
documents_to_add = [chunk["content"] for chunk in intelligent_chunks]
metadatas_to_add = [chunk["metadata"] for chunk in intelligent_chunks]

# Creazione ID unici per ogni chunk
ids_to_add = [f"chunk_{i}_page_{chunk['metadata']['page']}" for i, chunk in enumerate(intelligent_chunks)]

print(f"Inizio l'indicizzazione di {len(documents_to_add)} chunk...")

start_time = time.time()

# --- Aggiunta dei dati alla collection --- 
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

# --- Domande ---
queries = [
    "Dove si parla di Ecosystem?",
    "dove è la tabella?"
]

# --- Esecuzione delle Query ---
print(f"\nEseguo {len(queries)} query in batch...")

# Estrazione di 3 risultati per ogni query
results = collection.query(
    query_texts=queries,
    n_results=3 
)

# --- Stampa dei Risultati ---
print("\n--- Risultati della Ricerca Trovati ---")

if not results['documents']:
    print("Nessun risultato trovato.")
else:

    for q_idx, query in enumerate(queries):
        print(f"\n==============================================")
        print(f"RISULTATI PER LA QUERY: '{query}'")
        print(f"==============================================")
        
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
