def run_queries(collection, queries, n_results=2):
    """
    Esegue le query sulla collection ChromaDB e stampa in modo leggibile i risultati.
    Mostra: distanza semantica, pagina, tipo e contenuto di ogni chunk.
    """
    print(f"\nEseguo {len(queries)} query...")
    results = collection.query(query_texts=queries, n_results=n_results)

    for q_idx, query in enumerate(queries):
        print(f"\n{'='*50}")
        print(f"RISULTATI PER: '{query}'")
        print(f"{'='*50}")

        docs = results['documents'][q_idx]
        metas = results['metadatas'][q_idx]
        dists = results['distances'][q_idx]

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
            print(f"\n--- Risultato {i+1} (dist={dist:.4f}) ---")
            print(f"PDF: {meta.get('source_pdf', 'N/A')} | Pagina: {meta.get('page', 'N/A')} | Tipo: {meta.get('type', 'N/A')}")
            print("Contenuto:")
            for line in doc.strip().split('\n'):
                print(f"  {line}")
