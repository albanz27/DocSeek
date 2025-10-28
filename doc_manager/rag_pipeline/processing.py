from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

MAX_TEXT_CHUNK_SIZE = 500
CHUNK_OVERLAP_SIZE = 50 

last_chunk_content = "" # Variabile globale per memorizzare il contenuto dell'ultimo chunk di testo

def flush_text_buffer(buffer, page_num, all_chunks_list):
    """
    Unisce il testo nel buffer e lo aggiunge come un unico chunk.
    Aggiorna la variabile globale 'last_chunk_content' per l'overlap.
    """
    global last_chunk_content
    if buffer:
        content = "\n".join(buffer)
        all_chunks_list.append({
            "content": content,
            "metadata": {"page": page_num, "type": "text"}
        })
        # Memorizza il contenuto dell'ultimo chunk per la sovrapposizione
        last_chunk_content = content
    buffer.clear()

def add_overlap_to_buffer(buffer):
    """
    Aggiunge una sezione del contenuto dell'ultimo chunk all'inizio del nuovo buffer
    per creare l'overlap contestuale.
    """
    global last_chunk_content
    if last_chunk_content:
        # Prende gli ultimi CHUNK_OVERLAP_SIZE caratteri
        overlap_text = last_chunk_content[-CHUNK_OVERLAP_SIZE:]
        # Aggiunge una riga esplicita all'inizio del nuovo chunk
        buffer.append(f"--- CONTINUA DA CONTESTO PRECEDENTE: {overlap_text} ---")

def convert_table_to_markdown(table_data, page_num: int) -> str:
    """
    Converte i dati della tabella Docling in una stringa Markdown.
    """
    grid = table_data.grid
    if not grid:
        return f"Tabella vuota a pagina {page_num}"

    markdown = f"Tabella a pagina {page_num}:\n"

    # Header della tabella
    markdown += "| " + " | ".join(cell.text for cell in grid[0]) + " |\n"
    # Separatore Markdown
    markdown += "| " + " | ".join(["---"] * len(grid[0])) + " |\n"
    # Righe del corpo
    for row in grid[1:]:
        markdown += "| " + " | ".join(cell.text for cell in row) + " |\n"

    return markdown

def create_chunks(doc):
    """
    Converte un documento Docling in chunk logici:
    - testo (TEXT, LIST, SECTION_HEADER)
    - tabelle 
    - immagini 
    """
    global last_chunk_content
    all_chunks, text_buffer, current_page = [], [], 1
    last_chunk_content = "" 

    # Costruzione di una mappa dei riferimenti per accedere rapidamente agli oggetti
    item_map = {item.self_ref: item for item in (doc.texts + doc.tables + doc.pictures)}

    # Iterazione sull'ordine logico del documento
    for ref_item in doc.body.children:
        cref = ref_item.cref
        if cref not in item_map:
            continue  # ignora riferimenti non validi
        item = item_map[cref]

        # Aggiorna il numero di pagina corrente
        if item.prov:
            current_page = item.prov[0].page_no

        item_type = item.label.name

        if item_type in ['TEXT', 'SECTION_HEADER', 'LIST']:
            new_text = item.text
            
            # Calcola la lunghezza approssimativa del buffer SE aggiungiamo il nuovo testo
            # Consideriamo anche l'overlap se presente
            current_buffer_length = len("\n".join(text_buffer)) if text_buffer else 0
            new_line_length = len(new_text) + 1

            if current_buffer_length + new_line_length > MAX_TEXT_CHUNK_SIZE:
                # 1. Se sforiamo, finalizza il chunk corrente
                flush_text_buffer(text_buffer, current_page, all_chunks)
                
                # 2. Aggiungi la sovrapposizione al buffer appena svuotato
                add_overlap_to_buffer(text_buffer)
                
                # 3. Inizia il nuovo chunk con il testo corrente
                text_buffer.append(new_text)
            else:
                # Altrimenti, aggiungi il nuovo testo al buffer corrente
                text_buffer.append(new_text)

        elif item_type == 'TABLE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            last_chunk_content = ""
            table_md = convert_table_to_markdown(item.data, current_page)
            all_chunks.append({
                "content": table_md,
                "metadata": {"page": current_page, "type": "table"}
            })

        elif item_type == 'PICTURE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            last_chunk_content = ""
            desc = "Immagine rilevata (nessuna didascalia trovata)"
            if item.captions:
                caption_texts = []
                for ref in item.captions:
                    if ref.cref in item_map:
                        caption_texts.append(item_map[ref.cref].text)
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

def convert_pdf_to_doc(filename: str):
    """
    Converte un PDF in documento Docling pronto per l'elaborazione.
    Imposta le opzioni della pipeline:
      - riconoscimento delle tabelle
      - estrazione delle immagini
    """
    options = PdfPipelineOptions(do_table_structure=True, generate_picture_images=True)
    pdf_format = PdfFormatOption(pipeline_options=options)
    converter = DocumentConverter(format_options={"pdf": pdf_format})
    print(f"Inizio analisi strutturata di: {filename}")
    result = converter.convert(filename)
    return result.document
