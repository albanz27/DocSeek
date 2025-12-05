import Levenshtein
from typing import Dict, Tuple
import json
from pathlib import Path


def calculate_cer(ground_truth: str, predicted: str) -> float:
    if len(ground_truth) == 0:
        return 0.0 if len(predicted) == 0 else 100.0
    
    distance = Levenshtein.distance(ground_truth, predicted)
    cer = (distance / len(ground_truth)) * 100
    
    return cer


def calculate_wer(ground_truth: str, predicted: str) -> float:
    gt_words = ground_truth.split()
    pred_words = predicted.split()
    
    if len(gt_words) == 0:
        return 0.0 if len(pred_words) == 0 else 100.0
    
    gt_string = ' '.join(gt_words)
    pred_string = ' '.join(pred_words)
    distance = Levenshtein.distance(gt_string, pred_string)
    wer = (distance / len(gt_string)) * 100
    
    return wer


def calculate_accuracy(ground_truth: str, predicted: str) -> float:
    cer = calculate_cer(ground_truth, predicted)
    accuracy = 100 - cer
    
    return max(0.0, accuracy)


def calculate_all_metrics(ground_truth: str, predicted: str) -> Dict[str, float]:
    cer = calculate_cer(ground_truth, predicted)
    wer = calculate_wer(ground_truth, predicted)
    accuracy = calculate_accuracy(ground_truth, predicted)
    
    return {
        'CER': round(cer, 2),
        'WER': round(wer, 2),
        'Accuracy': round(accuracy, 2)
    }


def evaluate_dataset(dataset_path: str, ocr_results_path: str) -> Dict[str, any]:
    dataset_dir = Path(dataset_path)
    results_dir = Path(ocr_results_path)
    
    all_metrics = []
    detailed_results = []
    
    for gt_file in sorted(dataset_dir.glob('*.txt')):
        ocr_file = results_dir / gt_file.name
        
        with open(gt_file, 'r', encoding='utf-8') as f:
            ground_truth = f.read().strip()
        
        with open(ocr_file, 'r', encoding='utf-8') as f:
            predicted = f.read().strip()
        
        metrics = calculate_all_metrics(ground_truth, predicted)
        metrics['filename'] = gt_file.name
        
        all_metrics.append(metrics)
        detailed_results.append(metrics)
        
        print(f"Processed {gt_file.name}: CER={metrics['CER']:.2f}%, WER={metrics['WER']:.2f}%, Acc={metrics['Accuracy']:.2f}%")
    
    if all_metrics:
        avg_cer = sum(m['CER'] for m in all_metrics) / len(all_metrics)
        avg_wer = sum(m['WER'] for m in all_metrics) / len(all_metrics)
        avg_accuracy = sum(m['Accuracy'] for m in all_metrics) / len(all_metrics)
        
        results = {
            'average': {
                'CER': round(avg_cer, 2),
                'WER': round(avg_wer, 2),
                'Accuracy': round(avg_accuracy, 2)
            },
            'num_samples': len(all_metrics),
            'detailed_results': detailed_results
        }
    else:
        results = {
            'average': {'CER': 0.0, 'WER': 0.0, 'Accuracy': 0.0},
            'num_samples': 0,
            'detailed_results': []
        }
    
    return results


def save_results_to_json(results: Dict, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_path}")


# Funzione per formattare i risultati
def format_results_table(results: Dict) -> str:

    output = []
    output.append("\n" + "="*60)
    output.append("OCR PERFORMANCE EVALUATION RESULTS")
    output.append("="*60)
    output.append(f"\nNumber of samples evaluated: {results['num_samples']}")
    output.append("\n" + "-"*60)
    output.append("AVERAGE METRICS:")
    output.append("-"*60)
    output.append(f"  Character Error Rate (CER):  {results['average']['CER']:.2f}%")
    output.append(f"  Word Error Rate (WER):       {results['average']['WER']:.2f}%")
    output.append(f"  Accuracy:                    {results['average']['Accuracy']:.2f}%")
    output.append("="*60 + "\n")
    
    return '\n'.join(output)