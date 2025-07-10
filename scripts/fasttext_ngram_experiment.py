"""
Script untuk eksperimen parameter n-gram pada model FastText
Fase 1: Optimasi Parameter N-gram dari fasttext_improvement_tasks.md
"""
import os
import sys
import json
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing import process_quran_data
from backend.fasttext_model import FastTextModel

class FastTextNgramExperiment:
    """
    Kelas untuk melakukan eksperimen parameter n-gram pada model FastText
    """
    
    def __init__(self, dataset_dir: str = None):
        """
        Inisialisasi eksperimen
        
        Args:
            dataset_dir: Path ke direktori dataset Al-Quran
        """
        if dataset_dir is None:
            dataset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
        
        self.dataset_dir = dataset_dir
        self.results = []
        self.best_config = None
        
        # Parameter n-gram yang akan dieksperimen
        self.min_n_values = [2, 3]
        self.max_n_values = [4, 5, 6]
        
        # Dataset evaluasi
        self.evaluation_queries = self._create_evaluation_queries()
        
    def _create_evaluation_queries(self) -> List[Dict[str, Any]]:
        """
        Membuat dataset evaluasi yang mencakup berbagai jenis query
        """
        queries = [
            # Query umum
            {"query": "shalat", "category": "ibadah", "expected_verses": ["2:3", "2:43", "2:110"]},
            {"query": "puasa", "category": "ibadah", "expected_verses": ["2:183", "2:184", "2:185"]},
            {"query": "zakat", "category": "ibadah", "expected_verses": ["2:43", "2:110", "2:177"]},
            
            # Query dengan variasi morfologi
            {"query": "berdoa", "category": "morfologi", "expected_verses": ["2:186", "40:60"]},
            {"query": "mendoakan", "category": "morfologi", "expected_verses": ["9:103", "9:99"]},
            {"query": "doa", "category": "morfologi", "expected_verses": ["2:186", "40:60"]},
            
            # Query jarang/domain-specific
            {"query": "malaikat", "category": "domain", "expected_verses": ["2:30", "2:34", "2:98"]},
            {"query": "nabi", "category": "domain", "expected_verses": ["2:136", "3:84", "4:136"]},
            {"query": "rasul", "category": "domain", "expected_verses": ["2:136", "3:84", "4:136"]},
            
            # Query dengan kata majemuk
            {"query": "hari kiamat", "category": "majemuk", "expected_verses": ["2:85", "3:185"]},
            {"query": "surga neraka", "category": "majemuk", "expected_verses": ["2:25", "2:39"]},
            
            # Query dengan kata asing
            {"query": "alhamdulillah", "category": "asing", "expected_verses": ["1:2", "6:1"]},
            {"query": "insyaallah", "category": "asing", "expected_verses": ["2:70", "18:23"]},
        ]
        
        return queries
    
    def _train_fasttext_model(self, min_n: int, max_n: int, corpus_path: str) -> str:
        """
        Melatih model FastText dengan parameter n-gram tertentu
        
        Args:
            min_n: Minimum n-gram size
            max_n: Maximum n-gram size
            corpus_path: Path ke file korpus training
            
        Returns:
            Path ke model yang dilatih
        """
        from gensim.models import FastText
        from gensim.models.fasttext import FastText as FastTextTrain
        
        # Baca korpus
        with open(corpus_path, 'r', encoding='utf-8') as f:
            sentences = [line.strip().split() for line in f if line.strip()]
        
        # Latih model FastText
        model = FastTextTrain(
            sentences,
            vector_size=200,
            window=5,
            min_count=1,
            min_n=min_n,
            max_n=max_n,
            workers=4,
            sg=1,  # Skip-gram
            epochs=10
        )
        
        # Simpan model
        model_path = f"models/fasttext/fasttext_min{min_n}_max{max_n}.model"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        model.save(model_path)
        
        return model_path
    
    def _evaluate_model(self, model: FastTextModel, query: str, expected_verses: List[str]) -> Dict[str, Any]:
        """
        Evaluasi model pada query tertentu
        
        Args:
            model: Model FastText yang sudah dimuat
            query: Query untuk evaluasi
            expected_verses: Daftar ayat yang diharapkan sebagai hasil
            
        Returns:
            Dictionary berisi metrik evaluasi
        """
        # Lakukan pencarian
        results = model.search(query, limit=20, threshold=0.3)
        
        # Hitung metrik
        retrieved_verses = [r['verse_id'] for r in results]
        relevant_verses = expected_verses
        
        # Precision, Recall, F1
        relevant_retrieved = len(set(retrieved_verses) & set(relevant_verses))
        precision = relevant_retrieved / len(retrieved_verses) if retrieved_verses else 0
        recall = relevant_retrieved / len(relevant_verses) if relevant_verses else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # MAP (Mean Average Precision)
        ap = 0
        if relevant_verses:
            for i, verse_id in enumerate(retrieved_verses):
                if verse_id in relevant_verses:
                    ap += (len([v for v in retrieved_verses[:i+1] if v in relevant_verses])) / (i + 1)
            ap /= len(relevant_verses)
        
        # NDCG (Normalized Discounted Cumulative Gain)
        dcg = 0
        idcg = 0
        for i, verse_id in enumerate(retrieved_verses):
            relevance = 1 if verse_id in relevant_verses else 0
            dcg += relevance / np.log2(i + 2)
        
        # Ideal DCG
        for i in range(min(len(relevant_verses), len(retrieved_verses))):
            idcg += 1 / np.log2(i + 2)
        
        ndcg = dcg / idcg if idcg > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'map': ap,
            'ndcg': ndcg,
            'retrieved_count': len(retrieved_verses),
            'relevant_count': len(relevant_verses),
            'relevant_retrieved_count': relevant_retrieved
        }
    
    def run_experiment(self) -> Dict[str, Any]:
        """
        Menjalankan eksperimen parameter n-gram
        
        Returns:
            Dictionary berisi hasil eksperimen
        """
        print("=== FastText N-gram Parameter Experiment ===")
        
        # Proses data Al-Quran
        print("Memproses data Al-Quran...")
        preprocessed_verses = process_quran_data(dataset_dir=self.dataset_dir)
        
        # Buat korpus untuk training
        corpus_path = "temp_corpus.txt"
        with open(corpus_path, 'w', encoding='utf-8') as f:
            for verse_id, verse_info in preprocessed_verses.items():
                tokens = verse_info['tokens']
                f.write(' '.join(tokens) + '\n')
        
        experiment_results = []
        
        # Eksperimen dengan berbagai kombinasi parameter
        for min_n in self.min_n_values:
            for max_n in self.max_n_values:
                if min_n >= max_n:
                    continue
                
                print(f"\nEksperimen dengan min_n={min_n}, max_n={max_n}")
                
                try:
                    # Latih model dengan parameter tertentu
                    model_path = self._train_fasttext_model(min_n, max_n, corpus_path)
                    
                    # Muat model
                    model = FastTextModel(model_path=model_path)
                    model.load_model()
                    model.create_verse_vectors(preprocessed_verses)
                    
                    # Evaluasi pada semua query
                    query_results = []
                    for query_info in self.evaluation_queries:
                        query = query_info['query']
                        expected_verses = query_info['expected_verses']
                        category = query_info['category']
                        
                        metrics = self._evaluate_model(model, query, expected_verses)
                        metrics['query'] = query
                        metrics['category'] = category
                        query_results.append(metrics)
                    
                    # Hitung rata-rata metrik
                    avg_metrics = {
                        'min_n': min_n,
                        'max_n': max_n,
                        'avg_precision': np.mean([r['precision'] for r in query_results]),
                        'avg_recall': np.mean([r['recall'] for r in query_results]),
                        'avg_f1': np.mean([r['f1'] for r in query_results]),
                        'avg_map': np.mean([r['map'] for r in query_results]),
                        'avg_ndcg': np.mean([r['ndcg'] for r in query_results]),
                        'query_results': query_results
                    }
                    
                    experiment_results.append(avg_metrics)
                    print(f"  Avg Precision: {avg_metrics['avg_precision']:.4f}")
                    print(f"  Avg Recall: {avg_metrics['avg_recall']:.4f}")
                    print(f"  Avg F1: {avg_metrics['avg_f1']:.4f}")
                    print(f"  Avg MAP: {avg_metrics['avg_map']:.4f}")
                    print(f"  Avg NDCG: {avg_metrics['avg_ndcg']:.4f}")
                    
                except Exception as e:
                    print(f"  Error pada eksperimen min_n={min_n}, max_n={max_n}: {e}")
                    continue
        
        # Bersihkan file temporary
        if os.path.exists(corpus_path):
            os.remove(corpus_path)
        
        # Simpan hasil
        self.results = experiment_results
        self._save_results()
        self._find_best_config()
        
        return {
            'results': experiment_results,
            'best_config': self.best_config
        }
    
    def _save_results(self):
        """
        Menyimpan hasil eksperimen ke file
        """
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Simpan hasil dalam format JSON
        results_file = os.path.join(results_dir, "fasttext_ngram_experiment_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Simpan hasil dalam format CSV
        csv_data = []
        for result in self.results:
            row = {
                'min_n': result['min_n'],
                'max_n': result['max_n'],
                'avg_precision': result['avg_precision'],
                'avg_recall': result['avg_recall'],
                'avg_f1': result['avg_f1'],
                'avg_map': result['avg_map'],
                'avg_ndcg': result['avg_ndcg']
            }
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join(results_dir, "fasttext_ngram_experiment_results.csv")
        df.to_csv(csv_file, index=False)
        
        print(f"\nHasil eksperimen disimpan di:")
        print(f"  JSON: {results_file}")
        print(f"  CSV: {csv_file}")
    
    def _find_best_config(self):
        """
        Menemukan konfigurasi terbaik berdasarkan F1-score
        """
        if not self.results:
            return
        
        best_result = max(self.results, key=lambda x: x['avg_f1'])
        self.best_config = {
            'min_n': best_result['min_n'],
            'max_n': best_result['max_n'],
            'avg_f1': best_result['avg_f1'],
            'avg_precision': best_result['avg_precision'],
            'avg_recall': best_result['avg_recall'],
            'avg_map': best_result['avg_map'],
            'avg_ndcg': best_result['avg_ndcg']
        }
        
        print(f"\n=== KONFIGURASI TERBAIK ===")
        print(f"min_n: {self.best_config['min_n']}")
        print(f"max_n: {self.best_config['max_n']}")
        print(f"Avg F1: {self.best_config['avg_f1']:.4f}")
        print(f"Avg Precision: {self.best_config['avg_precision']:.4f}")
        print(f"Avg Recall: {self.best_config['avg_recall']:.4f}")
        print(f"Avg MAP: {self.best_config['avg_map']:.4f}")
        print(f"Avg NDCG: {self.best_config['avg_ndcg']:.4f}")
    
    def create_visualization(self):
        """
        Membuat visualisasi hasil eksperimen
        """
        if not self.results:
            print("Tidak ada hasil untuk divisualisasikan")
            return
        
        # Buat DataFrame
        df = pd.DataFrame(self.results)
        
        # Buat plot
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: F1 Score
        pivot_f1 = df.pivot(index='min_n', columns='max_n', values='avg_f1')
        sns.heatmap(pivot_f1, annot=True, fmt='.4f', cmap='YlOrRd', ax=axes[0,0])
        axes[0,0].set_title('Average F1 Score')
        axes[0,0].set_xlabel('max_n')
        axes[0,0].set_ylabel('min_n')
        
        # Plot 2: Precision
        pivot_precision = df.pivot(index='min_n', columns='max_n', values='avg_precision')
        sns.heatmap(pivot_precision, annot=True, fmt='.4f', cmap='YlOrRd', ax=axes[0,1])
        axes[0,1].set_title('Average Precision')
        axes[0,1].set_xlabel('max_n')
        axes[0,1].set_ylabel('min_n')
        
        # Plot 3: Recall
        pivot_recall = df.pivot(index='min_n', columns='max_n', values='avg_recall')
        sns.heatmap(pivot_recall, annot=True, fmt='.4f', cmap='YlOrRd', ax=axes[1,0])
        axes[1,0].set_title('Average Recall')
        axes[1,0].set_xlabel('max_n')
        axes[1,0].set_ylabel('min_n')
        
        # Plot 4: MAP
        pivot_map = df.pivot(index='min_n', columns='max_n', values='avg_map')
        sns.heatmap(pivot_map, annot=True, fmt='.4f', cmap='YlOrRd', ax=axes[1,1])
        axes[1,1].set_title('Average MAP')
        axes[1,1].set_xlabel('max_n')
        axes[1,1].set_ylabel('min_n')
        
        plt.tight_layout()
        
        # Simpan plot
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        plot_file = os.path.join(results_dir, "fasttext_ngram_experiment_visualization.png")
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"Visualisasi disimpan di: {plot_file}")
        
        plt.show()

def main():
    """
    Main function untuk menjalankan eksperimen
    """
    print("=== FastText N-gram Parameter Experiment ===")
    
    # Buat eksperimen
    experiment = FastTextNgramExperiment()
    
    # Jalankan eksperimen
    start_time = time.time()
    results = experiment.run_experiment()
    end_time = time.time()
    
    print(f"\nEksperimen selesai dalam {end_time - start_time:.2f} detik")
    
    # Buat visualisasi
    experiment.create_visualization()
    
    print("\nEksperimen parameter n-gram FastText selesai!")

if __name__ == "__main__":
    main() 