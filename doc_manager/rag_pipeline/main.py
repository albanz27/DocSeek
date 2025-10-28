from doc_manager.rag_pipeline.processing import convert_pdf_to_doc, create_chunks
from doc_manager.rag_pipeline.embedding import init_chromadb, add_chunks_to_db
from doc_manager.rag_pipeline.search import run_queries

PDF_FILES = [
    "data/test_document2.pdf",
    "data/test_document.pdf"
]
COLLECTION_NAME = "docling_paper"
ALL_CHUNKS = []

for pdf in PDF_FILES:
    # 1 Conversione PDF -> Docling
    document = convert_pdf_to_doc(pdf)

    # 2️ Creazione dei chunk logici
    chunks = create_chunks(document)

    # Inserimento metadata per indicare da quale PDF proviene il chunk
    for c in chunks:
        c["metadata"]["source_pdf"] = pdf

    ALL_CHUNKS.extend(chunks)

print(f"Totale chunk creati da tutti i PDF: {len(ALL_CHUNKS)}")

# 3️ Setup del DB e indicizzazione
collection = init_chromadb(COLLECTION_NAME)
add_chunks_to_db(collection, ALL_CHUNKS)

# 4️ Query di esempio
queries = ["Dove si parla di Ecosystem?",
            "Dove è la tabella dei confronti?",
            "Dove si parla di formula detection?"]
run_queries(collection, queries)
