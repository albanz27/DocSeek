import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_results(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_metrics_by_document(results, output_dir):
    """
    grafico dettagliato per ogni singolo documento.
    """
    detailed = results['detailed_results']
    
    filenames = [r['filename'] for r in detailed]
    cer_values = [r['CER'] for r in detailed]
    wer_values = [r['WER'] for r in detailed]
    acc_values = [r['Accuracy'] for r in detailed]
    
    short_names = [f[:10] + '..' if len(f) > 12 else f for f in filenames]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x = np.arange(len(filenames))
    width = 0.25
    
    bars1 = ax.bar(x - width, cer_values, width, label='CER (Caratteri)', color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x, wer_values, width, label='WER (Parole)', color='#3498db', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars3 = ax.bar(x + width, acc_values, width, label='Accuracy', color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=0.5)
    
    def add_values(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=7, fontweight='bold', rotation=0)
    
    add_values(bars1)
    add_values(bars2)
    add_values(bars3)
    
    ax.set_ylabel('Percentuale (%)', fontsize=12, fontweight='bold')
    ax.set_title('Performance OCR per Documento', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(short_names, rotation=45, ha='right')
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    ax.set_ylim(0, 110)
    
    plt.tight_layout()
    output_path = output_dir / '1_metriche_per_documento.png'
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Salvato: {output_path.name}")

def plot_average_metrics(results, output_dir):
    """
    Grafico a barre delle medie totali.
    """
    avg = results['average']
    
    metrics = ['CER', 'WER', 'Accuracy']
    values = [avg['CER'], avg['WER'], avg['Accuracy']]
    colors = ['#e74c3c', '#3498db', '#2ecc71']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    bars = ax.bar(metrics, values, color=colors, alpha=0.85, edgecolor='black', width=0.6)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{height:.2f}%',
                ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('Percentuale Media (%)', fontsize=12)
    ax.set_title('Medie Complessive del Dataset', fontsize=15, fontweight='bold', pad=20)
    ax.set_ylim(0, 115)
    
    ax.grid(axis='x')
    
    plt.tight_layout()
    output_path = output_dir / '2_medie_complessive.png'
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Salvato: {output_path.name}")

def plot_improved_pie_chart(results, output_dir):
    """
    Grafico a torta
    """
    detailed = results['detailed_results']
    accuracies = [r['Accuracy'] for r in detailed]
    
    tiers = {
        'Eccellente (98-100%)': 0,
        'Buono (90-98%)': 0,
        'Sufficiente (80-90%)': 0,
        'Insufficiente (<80%)': 0
    }
    
    colors_map = {
        'Eccellente (98-100%)': '#27ae60', 
        'Buono (90-98%)': '#2ecc71',
        'Sufficiente (80-90%)': '#f1c40f',
        'Insufficiente (<80%)': '#e74c3c'
    }
    
    for acc in accuracies:
        if acc >= 98: tiers['Eccellente (98-100%)'] += 1
        elif acc >= 90: tiers['Buono (90-98%)'] += 1
        elif acc >= 80: tiers['Sufficiente (80-90%)'] += 1
        else: tiers['Insufficiente (<80%)'] += 1
    
    labels = [k for k, v in tiers.items() if v > 0]
    sizes = [v for k, v in tiers.items() if v > 0]
    colors = [colors_map[k] for k in labels]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct='%1.1f%%',
                                      startangle=90, colors=colors,
                                      pctdistance=0.85, explode=[0.02]*len(sizes),
                                      textprops=dict(color="black", weight="bold"))
    
    centre_circle = plt.Circle((0,0), 0.65, fc='white')
    fig.gca().add_artist(centre_circle)
    
    total = len(accuracies)
    ax.text(0, 0, f"Totale:\n{total} Doc", ha='center', va='center', fontsize=12, fontweight='bold', color='#555')
    
    ax.legend(wedges, labels,
              title="Fasce di Qualità",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))
    
    ax.set_title('Distribuzione Qualità OCR', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / '3_distribuzione_qualita_pie.png'
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Salvato: {output_path.name}")

def plot_summary_table(results, output_dir):
    """
    Tabella Riassuntiva
    """
    detailed = results['detailed_results']
    
    fig, ax = plt.subplots(figsize=(12, len(detailed)*0.5 + 2))
    ax.axis('tight')
    ax.axis('off')
    
    table_data = []
    for r in detailed:
        name = r['filename']
        if len(name) > 25: name = name[:22] + '...'
            
        table_data.append([
            name,
            f"{r['CER']:.2f}%",
            f"{r['WER']:.2f}%",
            f"{r['Accuracy']:.2f}%",
            r['gt_length'],
            r['ocr_length']
        ])
    
    avg = results['average']
    table_data.append(['MEDIA', f"{avg['CER']:.2f}%", f"{avg['WER']:.2f}%", f"{avg['Accuracy']:.2f}%", '-', '-'])
    
    headers = ['Documento', 'CER', 'WER', 'Accuracy', 'GT Len', 'OCR Len']
    
    table = ax.table(cellText=table_data, colLabels=headers,
                     cellLoc='center', loc='center',
                     colWidths=[0.35, 0.1, 0.1, 0.1, 0.1, 0.1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    for i in range(len(table_data)):
        if i == len(table_data)-1:
            for j in range(len(headers)):
                table[(i+1, j)].set_facecolor('#f1c40f')
                table[(i+1, j)].set_text_props(weight='bold')
        else:
            bg_color = '#f8f9fa' if i % 2 == 0 else '#ffffff'
            for j in range(len(headers)):
                table[(i+1, j)].set_facecolor(bg_color)
                
    plt.title('Tabella Dettagliata Risultati', fontsize=14, fontweight='bold', pad=10)
    plt.tight_layout()
    output_path = output_dir / '4_tabella_riassuntiva.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Salvato: {output_path.name}")

def generate_final_plots(json_path, output_dir):
    json_path = Path(json_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n--- GENERAZIONE GRAFICI FINALI ---")
    results = load_results(json_path)
    
    plot_metrics_by_document(results, output_dir)
    plot_average_metrics(results, output_dir)
    plot_improved_pie_chart(results, output_dir)
    plot_summary_table(results, output_dir)
    
    print("\nOperazione completata! Grafici salvati in:", output_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python script.py <json_file> <output_dir>")
        sys.exit(1)
    
    generate_final_plots(sys.argv[1], sys.argv[2])