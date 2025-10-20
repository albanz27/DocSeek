from a_processing import convert_pdf_to_doc, create_chunks
from b_embedding import init_chromadb, add_chunks_to_db
from c_search import run_queries

PDF_FILENAME = "data/test_document2.pdf"
COLLECTION_NAME = "docling_paper"

# 1 Conversione PDF -> Docling
document = convert_pdf_to_doc(PDF_FILENAME)

# 2️ Creazione dei chunk logici
chunks = create_chunks(document)
print(f"Creati {len(chunks)} chunk logici.")

# 3️ Setup del DB e indicizzazione
collection = init_chromadb(COLLECTION_NAME)
add_chunks_to_db(collection, chunks)

# 4️ Query di esempio
queries = ["Dove si parla di Ecosystem?", "dove è la tabella?"]
run_queries(collection, queries)
