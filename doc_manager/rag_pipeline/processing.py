from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from typing import List, Dict, Any
from .config import get_chunk_size, get_chunk_overlap

MAX_TEXT_CHUNK_SIZE = get_chunk_size()
CHUNK_OVERLAP_SIZE = get_chunk_overlap()


LAST_CHUNK_CONTENT = "" 

def flush_text_buffer(buffer, page_num, all_chunks_list):
    """Unisce il testo nel buffer e lo aggiunge come un unico chunk."""
    global LAST_CHUNK_CONTENT
    if buffer:
        content = "\n".join(buffer)
        all_chunks_list.append({
            "content": content,
            "metadata": {"page": page_num, "type": "text"}
        })
        LAST_CHUNK_CONTENT = content
    buffer.clear()

def add_overlap_to_buffer(buffer):
    """
    Aggiunge una sezione del contenuto dell'ultimo chunk all'inizio del nuovo buffer
    per creare l'overlap contestuale.
    """
    global LAST_CHUNK_CONTENT
    if LAST_CHUNK_CONTENT:
        overlap_text = LAST_CHUNK_CONTENT[-CHUNK_OVERLAP_SIZE:]
        buffer.append(overlap_text)

def convert_table_to_markdown(table_data, page_num: int) -> str:
    """
    Converte i dati della tabella Docling in una stringa Markdown.
    """
    grid = table_data.grid
    if not grid:
        return f"Tabella vuota a pagina {page_num}"

    markdown = ""
    markdown += "| " + " | ".join(cell.text for cell in grid[0]) + " |\n"
    markdown += "| " + " | ".join(["---"] * len(grid[0])) + " |\n"
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
    global LAST_CHUNK_CONTENT
    all_chunks, text_buffer, current_page = [], [], 1
    LAST_CHUNK_CONTENT = "" 

    item_map = {item.self_ref: item for item in (doc.texts + doc.tables + doc.pictures)}

    for ref_item in doc.body.children:
        cref = ref_item.cref
        if cref not in item_map:
            continue  
        item = item_map[cref]

        if item.prov:
            current_page = item.prov[0].page_no

        item_type = item.label.name

        if item_type in ['TEXT', 'SECTION_HEADER', 'LIST']:
            new_text = item.text
            
            current_buffer_length = len("\n".join(text_buffer)) if text_buffer else 0
            new_line_length = len(new_text) + 1

            if current_buffer_length + new_line_length > MAX_TEXT_CHUNK_SIZE:
                flush_text_buffer(text_buffer, current_page, all_chunks)

                add_overlap_to_buffer(text_buffer)
                text_buffer.append(new_text)
            else:
                text_buffer.append(new_text)

        elif item_type == 'TABLE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            LAST_CHUNK_CONTENT = ""
            table_md = convert_table_to_markdown(item.data, current_page)
            all_chunks.append({
                "content": table_md,
                "metadata": {"page": current_page, "type": "table"}
            })

        elif item_type == 'PICTURE':
            flush_text_buffer(text_buffer, current_page, all_chunks)
            LAST_CHUNK_CONTENT = ""
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

    flush_text_buffer(text_buffer, current_page, all_chunks)
    return all_chunks


def create_chunks_scannedpdf(text, title, chunk_size=MAX_TEXT_CHUNK_SIZE, overlap=CHUNK_OVERLAP_SIZE):
    """
    Crea chunks da testo OCR
    """
    chunks = []
    
    heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
    page_separator_pattern = re.compile(r'={60}\nPAGINA\s+(\d+)\n={60}')
    pages = _split_by_pages(text, page_separator_pattern)
    
    for page_num, page_content in pages.items():
        table_ranges = _find_tables(page_content)
        
        # Processa contenuto della pagina
        last_pos = 0
        current_heading = None
        
        for table_start, table_end, table_content in table_ranges:
            if last_pos < table_start:
                text_section = page_content[last_pos:table_start].strip()
                if text_section:
                    heading_match = heading_pattern.search(text_section)
                    if heading_match:
                        current_heading = heading_match.group(1)
                    
                    # Pulisci Markdown dal testo
                    cleaned_text = _clean_markdown(text_section)
                    
                    if len(cleaned_text) <= chunk_size:
                        chunks.append({
                            "content": cleaned_text,
                            "metadata": {
                                "page": page_num,
                                "type": "text",
                                "chunk_type": "text",
                                "source_title": title,
                                "heading": current_heading
                            }
                        })
                    else:
                        text_chunks = _split_long_text(cleaned_text, chunk_size, overlap)
                        for i, chunk_text in enumerate(text_chunks):
                            chunks.append({
                                "content": chunk_text,
                                "metadata": {
                                    "page": page_num,
                                    "type": "text",
                                    "chunk_type": "text",
                                    "source_title": title,
                                    "heading": current_heading,
                                    "chunk_index": i,
                                    "is_continuation": i > 0
                                }
                            })
            
            chunks.append({
                "content": table_content,
                "metadata": {
                    "page": page_num,
                    "type": "table",
                    "chunk_type": "table",
                    "source_title": title,
                    "context_heading": current_heading
                }
            })
            
            last_pos = table_end
        
        if last_pos < len(page_content):
            remaining_text = page_content[last_pos:].strip()
            if remaining_text:
                heading_match = heading_pattern.search(remaining_text)
                if heading_match:
                    current_heading = heading_match.group(1)
                
                cleaned_text = _clean_markdown(remaining_text)
                
                if len(cleaned_text) <= chunk_size:
                    chunks.append({
                        "content": cleaned_text,
                        "metadata": {
                            "page": page_num,
                            "type": "text",
                            "chunk_type": "text",
                            "source_title": title,
                            "heading": current_heading
                        }
                    })
                else:
                    text_chunks = _split_long_text(cleaned_text, chunk_size, overlap)
                    for i, chunk_text in enumerate(text_chunks):
                        chunks.append({
                            "content": chunk_text,
                            "metadata": {
                                "page": page_num,
                                "type": "text",
                                "chunk_type": "text",
                                "source_title": title,
                                "heading": current_heading,
                                "chunk_index": i,
                                "is_continuation": i > 0
                            }
                        })
    
    text_chunks = sum(1 for c in chunks if c['metadata']['type'] == 'text')
    
    return chunks


def _split_by_pages(text: str, page_pattern) -> Dict[int, str]:
    """Divide il testo per pagine"""
    pages = {}
    matches = list(page_pattern.finditer(text))
    
    if not matches:
        return {1: text}
    
    for i, match in enumerate(matches):
        page_num = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        page_content = text[start:end].strip()
        pages[page_num] = page_content
    
    return pages


def _find_tables(text: str) -> List[tuple]:
    """Trova tutte le tabelle nel testo e ritorna (start, end, content)"""
    tables = []
    lines = text.split('\n')
    
    in_table = False
    table_start_line = 0
    table_lines = []
    
    for i, line in enumerate(lines):
        if '|' in line:
            if not in_table:
                in_table = True
                table_start_line = i
                table_lines = [line]
            else:
                table_lines.append(line)
        else:
            if in_table:
                table_content = '\n'.join(table_lines)
                start_pos = sum(len(l) + 1 for l in lines[:table_start_line])
                end_pos = start_pos + len(table_content)
                tables.append((start_pos, end_pos, table_content))
                
                in_table = False
                table_lines = []
    
    if in_table and table_lines:
        table_content = '\n'.join(table_lines)
        start_pos = sum(len(l) + 1 for l in lines[:table_start_line])
        end_pos = start_pos + len(table_content)
        tables.append((start_pos, end_pos, table_content))
    
    return tables


def _clean_markdown(text: str) -> str:
    """Rimuove formattazione Markdown dal testo"""
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE) 
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)  
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)  
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text) 
    text = re.sub(r'!\[.*?\]\(.+?\)', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'^[\-_\*]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def _split_long_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Divide testo lungo in chunk con overlap intelligente"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        if end < text_length:
            separators = ['\n\n', '\n', '. ', '。', '! ', '? ', ' ']
            search_start = max(start + chunk_size - 100, start)
            search_end = min(end + 100, text_length)
            search_text = text[search_start:search_end]
            
            best_split = None
            for separator in separators:
                relative_pos = search_text.rfind(separator)
                if relative_pos != -1:
                    absolute_pos = search_start + relative_pos + len(separator)
                    if start < absolute_pos <= end + 100:
                        best_split = absolute_pos
                        break
            
            if best_split:
                end = best_split
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


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