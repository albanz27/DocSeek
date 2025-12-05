import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk") 

def generate_comparison_plot(output_path='plots/confronto_rilevanza.png'):
    categories = [
        'Docling\n', 
        'DeepSeek-OCR\n'
    ]
    values = [0.6761, 0.5114] 
    
    colors = ["#de1212", "#0f36f5"] 

    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(categories, values, color=colors, alpha=0.9, width=0.6, edgecolor='black', linewidth=1)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.4f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='#333')

    ax.axhline(y=0.7, color='green', linestyle='--', alpha=0.3, label='Soglia "Molto Rilevante"')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.3, label='Soglia "Rilevante"')

    ax.set_ylim(0, 0.85) 
    ax.set_ylabel('Rilevanza', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Confronto Rilevanza Semantica: Nativo vs OCR', fontsize=16, fontweight='bold', pad=20)
    
    ax.grid(axis='x')
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#de1212', edgecolor='black', label='Docling'),
        Patch(facecolor='#0f36f5', edgecolor='black', label='DeepSeek-OCR')
    ]
    ax.legend(handles=legend_elements, loc='upper right', frameon=True, framealpha=0.9)

    plt.tight_layout()
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Grafico generato con successo: {output_path.absolute()}")

if __name__ == "__main__":
    generate_comparison_plot()