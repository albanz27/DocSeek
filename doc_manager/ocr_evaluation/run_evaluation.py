import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from doc_manager.ocr_evaluation.metrics import calculate_all_metrics
import requests
import time

print("\n" + "="*60)
print("VALUTAZIONE OCR - Dataset FUNSD")
print("="*60)

GPU_SERVER_URL = 'http://localhost:8000'
DATASET_PATH = Path('datasets/FUNSD')
RESULTS_PATH = Path('results')
RESULTS_PATH.mkdir(exist_ok=True)

def send_pdf_to_ocr(pdf_path, title):
    """Invia un PDF al server GPU per OCR"""
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            data = {
                'document_id': 'evaluation',
                'title': title
            }
            
            response = requests.post(
                f'{GPU_SERVER_URL}/api/ocr/process',
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('task_id')
            else:
                raise Exception(f"Server error: {response.status_code}")
                
    except Exception as e:
        raise Exception(f"Errore invio PDF: {e}")

def wait_for_ocr_completion(task_id, max_wait=300):
    """Attende il completamento dell'OCR"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f'{GPU_SERVER_URL}/api/ocr/status/{task_id}',
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                progress = result.get('progress', 0)
                
                if status == 'completed':
                    return result.get('text', '')
                elif status == 'failed':
                    error = result.get('error', 'Unknown error')
                    raise Exception(f"OCR failed: {error}")
                else:
                    print(f"    Stato: {status}, Progresso: {progress:.1f}%")
                    time.sleep(5)
            else:
                time.sleep(5)
                
        except Exception as e:
            print(f"Errore check status: {e}")
            time.sleep(5)
    
    raise Exception("Timeout: OCR non completato")

def evaluate_single_document(pdf_path, gt_path, doc_num, total_docs):
    """Valuta un singolo documento"""
    doc_name = pdf_path.stem
    
    print(f"\n[{doc_num}/{total_docs}] Documento: {doc_name}")
    print(f"PDF: {pdf_path.name}")
    print(f"Ground Truth: {gt_path.name}")
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        ground_truth = f.read().strip()
    
    print(f"  Ground truth: {len(ground_truth)} caratteri")
    
    print(f"  → Invio al server GPU...")
    try:
        task_id = send_pdf_to_ocr(pdf_path, doc_name)
        print(f"Task ID: {task_id}")
        print(f"Attendo completamento OCR...")
        
        ocr_text = wait_for_ocr_completion(task_id)
        print(f"OCR completato: {len(ocr_text)} caratteri")
        
        metrics = calculate_all_metrics(ground_truth, ocr_text)
        metrics['filename'] = doc_name
        metrics['gt_length'] = len(ground_truth)
        metrics['ocr_length'] = len(ocr_text)
        
        print(f"CER: {metrics['CER']:.2f}%")
        print(f"WER: {metrics['WER']:.2f}%")
        print(f"Accuracy: {metrics['Accuracy']:.2f}%")
        
        return metrics
        
    except Exception as e:
        print(f"Errore: {e}")
        return {
            'filename': doc_name,
            'error': str(e),
            'CER': None,
            'WER': None,
            'Accuracy': None
        }

def run_evaluation():
    """Esegue la valutazione completa"""
    
    print("\n[2/5] Verifica dataset...")
    pdfs_dir = DATASET_PATH / 'pdfs'
    gt_dir = DATASET_PATH / 'ground_truth'

    pdf_files = sorted(pdfs_dir.glob('*.pdf'))
    print(f"Trovati {len(pdf_files)} file PDF")
    
    print(f"\n[3/5] Valutazione OCR su {len(pdf_files)} documenti...")
    print("="*60)
    
    all_results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        gt_file = gt_dir / f"{pdf_file.stem}.txt"
        
        if not gt_file.exists():
            print(f"\n[{i}/{len(pdf_files)}] Ground truth non trovato: {pdf_file.stem}")
            continue
        
        result = evaluate_single_document(pdf_file, gt_file, i, len(pdf_files))
        all_results.append(result)
    
    print("\n[4/5] Calcolo statistiche...")
    valid_results = [r for r in all_results if r.get('CER') is not None]
    
    if not valid_results:
        print("Nessun risultato valido")
        return
    
    avg_cer = sum(r['CER'] for r in valid_results) / len(valid_results)
    avg_wer = sum(r['WER'] for r in valid_results) / len(valid_results)
    avg_acc = sum(r['Accuracy'] for r in valid_results) / len(valid_results)
    
    results = {
        'dataset_name': 'FUNSD',
        'num_samples': len(all_results),
        'num_successful': len(valid_results),
        'num_failed': len(all_results) - len(valid_results),
        'average': {
            'CER': round(avg_cer, 2),
            'WER': round(avg_wer, 2),
            'Accuracy': round(avg_acc, 2)
        },
        'detailed_results': all_results
    }
    
    print("\n[5/5] Salvataggio risultati...")
    output_file = RESULTS_PATH / 'funsd_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Risultati salvati in: {output_file}")
    
    # Stampa riepilogo
    print("\n" + "="*60)
    print("RISULTATI FINALI")
    print("="*60)
    print(f"Dataset:          FUNSD")
    print(f"Documenti totali: {len(all_results)}")
    print(f"Successi:         {len(valid_results)}")
    print(f"Falliti:          {len(all_results) - len(valid_results)}")
    print("-"*60)
    print(f"CER medio:        {avg_cer:.2f}%")
    print(f"WER medio:        {avg_wer:.2f}%")
    print(f"Accuracy media:   {avg_acc:.2f}%")
    print("="*60)
    
    return results

if __name__ == "__main__":
    try:
        run_evaluation()
        print("\nValutazione completata!")
        print("\nProva a generare i grafici con:")
        print("  python doc_manager\\ocr_evaluation\\generate_plots.py results\\funsd_results.json plots\\")
    except KeyboardInterrupt:
        print("\n\nValutazione interrotta dall'utente")
    except Exception as e:
        print(f"\nErrore: {e}")
        import traceback
        traceback.print_exc()