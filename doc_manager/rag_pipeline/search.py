def run_queries(collection, queries, n_results=3):
    """
    Esegue le query sulla collection ChromaDB e restituisce i risultati 
    in una lista strutturata per l'uso nel template Django.
    """
    if not queries:
        return []

    print(f"\nEseguo {len(queries)} query su ChromaDB...")
    print(f"DEBUG: Chunk totali nella collezione ChromaDB: {collection.count()}")
    results = collection.query(query_texts=queries, n_results=n_results)

    all_formatted_results = []
    
    for q_idx, query in enumerate(queries):
        docs = results['documents'][q_idx]
        metas = results['metadatas'][q_idx]
        dists = results['distances'][q_idx]

        print(f"DEBUG: Risultati trovati per la query '{query}': {len(docs)}")

        query_results = {
            'query': query,
            'chunks': []
        }

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
            # Usiamo 'source_title' e 'document_id' che abbiamo aggiunto nel tasks.py
            document_title = meta.get('source_title', meta.get('source_pdf', 'N/A'))
            document_id = meta.get('document_id', None)
            
            query_results['chunks'].append({
                'distance': dist,
                'document_title': document_title,
                'document_id': document_id,
                'page': meta.get('page', 'N/A'),
                'type': meta.get('type', 'N/A'),
                'content': doc.strip()
            })
        
        all_formatted_results.append(query_results)

    # Restituisce l'oggetto completo
    print(f"Query eseguite. Risultati formattati pronti per il template.")
    print(f"Numero totale di query elaborate: {len(all_formatted_results)}")

    print(f"DEBUG: Contenuto finale restituito a Django: {all_formatted_results}")
    return all_formatted_results