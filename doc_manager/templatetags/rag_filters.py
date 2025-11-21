import re
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='render_rag_content')
def render_rag_content(content, chunk_type):
    """
    Renderizza il contenuto RAG in base al tipo:
    - table: converte Markdown table in HTML table
    - image: mostra una card con descrizione immagine
    - text/ocr_text: formatta il testo con paragrafi
    """
    if not content:
        return ""
    
    if chunk_type == 'table':
        return mark_safe(render_markdown_table(content))
    elif chunk_type == 'image':
        return mark_safe(render_image_reference(content))
    else:
        return mark_safe(render_text_content(content))


def render_markdown_table(content):
    """
    Converte tabella Markdown in HTML table con Bootstrap styling.
    """
    # Usa markdown per convertire la tabella
    md = markdown.Markdown(extensions=['tables', 'nl2br'])
    html = md.convert(content)
    
    # Aggiungi classi Bootstrap alle tabelle
    html = html.replace('<table>', '<div class="table-responsive"><table class="table table-striped table-hover table-bordered table-sm">')
    html = html.replace('</table>', '</table></div>')
    html = html.replace('<thead>', '<thead class="table-primary">')
    
    return html


def render_image_reference(content):
    """
    Renderizza un riferimento a un'immagine con una card visiva.
    """
    # Estrai informazioni dall'immagine
    page_match = re.search(r'Pagina (\d+)', content)
    caption_match = re.search(r"Didascalia: '(.+?)'", content)
    
    page = page_match.group(1) if page_match else "N/A"
    caption = caption_match.group(1) if caption_match else "Nessuna didascalia"
    
    html = f"""
    <div class="image-reference-card">
        <div class="image-icon">
            <i class="fas fa-image fa-3x text-info"></i>
        </div>
        <div class="image-details">
            <h6 class="mb-1"><i class="fas fa-file-image me-1"></i> Immagine Rilevata</h6>
            <p class="mb-1"><strong>Pagina:</strong> {page}</p>
            <p class="mb-0"><strong>Didascalia:</strong> {caption}</p>
        </div>
    </div>
    """
    return html


def render_text_content(content):
    """
    Formatta il contenuto testuale con paragrafi e line breaks.
    """
    # Dividi in paragrafi basandoti su doppie newline
    paragraphs = content.split('\n\n')
    
    html_parts = []
    for para in paragraphs:
        if para.strip():
            # Converti singole newline in <br>
            para_html = para.replace('\n', '<br>')
            html_parts.append(f'<p class="text-content-para">{para_html}</p>')
    
    return ''.join(html_parts) if html_parts else f'<p class="text-content-para">{content}</p>'


@register.filter(name='highlight_query')
def highlight_query(text, query):
    """
    Evidenzia le occorrenze della query nel testo.
    """
    if not query or not text:
        return text
    
    # Cerca la query
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f'<mark class="search-highlight">{m.group(0)}</mark>', text)
    
    return mark_safe(highlighted)


@register.filter(name='format_distance')
def format_distance(distance):
    """
    Formatta la rilevanza semantica (1 - distanza) con colore basato sul valore.
    Più alto il valore, più rilevante è il risultato.
    """
    try:
        dist = float(distance)
        relevance = 1 - dist
        
        if relevance > 0.7:  
            color_class = "text-success"
            label = "Molto rilevante"
        elif relevance > 0.5:  
            color_class = "text-info"
            label = "Rilevante"
        elif relevance > 0.3: 
            color_class = "text-warning"
            label = "Moderatamente rilevante"
        else:
            color_class = "text-danger"
            label = "Poco rilevante"
        
        return mark_safe(f'<span class="{color_class}" title="{label}">{relevance:.4f}</span>')
    except (ValueError, TypeError):
        return distance


@register.filter(name='get_file_url')
def get_file_url(document_id):
    """
    Genera l'URL per visualizzare il documento.
    """
    from doc_manager.models import Document
    try:
        doc = Document.objects.get(pk=document_id)
        if doc.processed_file:
            return doc.processed_file.url
        return doc.file.url
    except Document.DoesNotExist:
        return "#"