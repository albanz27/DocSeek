from .config import get_n_results

DEFAULT_N_RESULTS = get_n_results()

def run_queries(collection, queries, n_results=DEFAULT_N_RESULTS):
    """
    Esegue le query sulla collection ChromaDB e restituisce i risultati 
    in una lista strutturata per l'uso nel template Django.
    """
    if not queries:
        return []

    results = collection.query(query_texts=queries, n_results=n_results)

    all_formatted_results = []
    
    for q_idx, query in enumerate(queries):
        docs = results['documents'][q_idx]
        metas = results['metadatas'][q_idx]
        dists = results['distances'][q_idx]

        query_results = {
            'query': query,
            'chunks': []
        }

        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
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

    print(f"Numero totale di query elaborate: {len(all_formatted_results)}")

    return all_formatted_results