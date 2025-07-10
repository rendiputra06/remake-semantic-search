"""
Script untuk mengupdate model FastText dengan parameter n-gram optimal
Fase 1.3: Implementasi Konfigurasi Optimal dari fasttext_improvement_tasks.md
"""
import os
import sys
import json
import shutil
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing import process_quran_data
from backend.fasttext_model import FastTextModel
from backend.initialize import initialize_fasttext

class FastTextOptimizer:
    """
    Kelas untuk mengoptimalkan model FastText dengan parameter n-gram terbaik
    """
    
    def __init__(self, optimal_config: Dict[str, Any] = None):
        """
        Inisialisasi optimizer
        
        Args:
            optimal_config: Konfigurasi optimal yang ditemukan dari eksperimen
        """
        self.optimal_config = optimal_config or {
            'min_n': 2,
            'max_n': 5,
            'vector_size': 200,
            'window': 5,
            'min_count': 1,
            'workers': 4,
            'sg': 1,  # Skip-gram
            'epochs': 15
        }
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = os.path.join(self.base_dir, 'models/fasttext')
        self.backup_dir = os.path.join(self.base_dir, 'models/fasttext/backup')
        
    def load_experiment_results(self, results_file: str = None) -> Dict[str, Any]:
        """
        Memuat hasil eksperimen untuk mendapatkan konfigurasi optimal
        
        Args:
            results_file: Path ke file hasil eksperimen
            
        Returns:
            Konfigurasi optimal
        """
        if results_file is None:
            results_file = os.path.join(self.base_dir, 'results/fasttext_ngram_experiment_results.json')
        
        if not os.path.exists(results_file):
            print(f"File hasil eksperimen tidak ditemukan: {results_file}")
            print("Menggunakan konfigurasi default...")
            return self.optimal_config
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Temukan konfigurasi dengan F1-score tertinggi
            best_result = max(results, key=lambda x: x['avg_f1'])
            
            optimal_config = {
                'min_n': best_result['min_n'],
                'max_n': best_result['max_n'],
                'vector_size': 200,
                'window': 5,
                'min_count': 1,
                'workers': 4,
                'sg': 1,
                'epochs': 15
            }
            
            print(f"Konfigurasi optimal ditemukan:")
            print(f"  min_n: {optimal_config['min_n']}")
            print(f"  max_n: {optimal_config['max_n']}")
            print(f"  Avg F1: {best_result['avg_f1']:.4f}")
            
            return optimal_config
            
        except Exception as e:
            print(f"Error memuat hasil eksperimen: {e}")
            print("Menggunakan konfigurasi default...")
            return self.optimal_config
    
    def backup_current_model(self):
        """
        Membuat backup model FastText yang ada
        """
        os.makedirs(self.backup_dir, exist_ok=True)
        
        current_model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        if os.path.exists(current_model_path):
            backup_path = os.path.join(self.backup_dir, f'fasttext_backup_{int(time.time())}.model')
            shutil.copy2(current_model_path, backup_path)
            print(f"Model saat ini dibackup ke: {backup_path}")
        else:
            print("Model FastText saat ini tidak ditemukan")
    
    def create_corpus_from_quran(self) -> str:
        """
        Membuat korpus training dari data Al-Quran
        
        Returns:
            Path ke file korpus
        """
        print("Membuat korpus training dari data Al-Quran...")
        
        # Proses data Al-Quran
        dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
        
        # Buat korpus
        corpus_path = os.path.join(self.base_dir, 'temp_quran_corpus.txt')
        with open(corpus_path, 'w', encoding='utf-8') as f:
            for verse_id, verse_info in preprocessed_verses.items():
                tokens = verse_info['tokens']
                f.write(' '.join(tokens) + '\n')
        
        print(f"Korpus training dibuat: {corpus_path}")
        print(f"Jumlah ayat: {len(preprocessed_verses)}")
        
        return corpus_path
    
    def train_optimized_model(self, corpus_path: str) -> str:
        """
        Melatih model FastText dengan parameter optimal
        
        Args:
            corpus_path: Path ke file korpus training
            
        Returns:
            Path ke model yang dilatih
        """
        from gensim.models.fasttext import FastText
        
        print("Melatih model FastText dengan parameter optimal...")
        
        # Baca korpus
        with open(corpus_path, 'r', encoding='utf-8') as f:
            sentences = [line.strip().split() for line in f if line.strip()]
        
        print(f"Jumlah kalimat dalam korpus: {len(sentences)}")
        
        # Latih model dengan parameter optimal
        model = FastText(
            sentences,
            vector_size=self.optimal_config['vector_size'],
            window=self.optimal_config['window'],
            min_count=self.optimal_config['min_count'],
            min_n=self.optimal_config['min_n'],
            max_n=self.optimal_config['max_n'],
            workers=self.optimal_config['workers'],
            sg=self.optimal_config['sg'],
            epochs=self.optimal_config['epochs']
        )
        
        # Simpan model
        model_path = os.path.join(self.models_dir, 'fasttext_optimized.model')
        os.makedirs(self.models_dir, exist_ok=True)
        model.save(model_path)
        
        print(f"Model optimal disimpan di: {model_path}")
        
        # Informasi model
        print(f"Ukuran vocabulary: {len(model.wv.key_to_index)}")
        print(f"Dimensi vektor: {model.vector_size}")
        print(f"Parameter n-gram: min_n={self.optimal_config['min_n']}, max_n={self.optimal_config['max_n']}")
        
        return model_path
    
    def evaluate_optimized_model(self, model_path: str) -> Dict[str, Any]:
        """
        Evaluasi model yang dioptimalkan
        
        Args:
            model_path: Path ke model yang dioptimalkan
            
        Returns:
            Hasil evaluasi
        """
        print("Evaluasi model yang dioptimalkan...")
        
        # Muat model
        model = FastTextModel(model_path=model_path)
        model.load_model()
        
        # Proses data Al-Quran
        dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
        
        # Buat vektor ayat
        model.create_verse_vectors(preprocessed_verses)
        
        # Query evaluasi
        test_queries = [
            "shalat", "puasa", "zakat", "berdoa", "malaikat", "nabi", "rasul"
        ]
        
        evaluation_results = {}
        
        for query in test_queries:
            results = model.search(query, limit=10, threshold=0.3)
            evaluation_results[query] = {
                'results_count': len(results),
                'top_similarity': results[0]['similarity'] if results else 0,
                'avg_similarity': np.mean([r['similarity'] for r in results]) if results else 0
            }
        
        # Hitung rata-rata metrik
        avg_results_count = np.mean([r['results_count'] for r in evaluation_results.values()])
        avg_top_similarity = np.mean([r['top_similarity'] for r in evaluation_results.values()])
        avg_similarity = np.mean([r['avg_similarity'] for r in evaluation_results.values()])
        
        overall_evaluation = {
            'avg_results_count': avg_results_count,
            'avg_top_similarity': avg_top_similarity,
            'avg_similarity': avg_similarity,
            'query_results': evaluation_results
        }
        
        print(f"Hasil evaluasi:")
        print(f"  Rata-rata jumlah hasil: {avg_results_count:.2f}")
        print(f"  Rata-rata similarity tertinggi: {avg_top_similarity:.4f}")
        print(f"  Rata-rata similarity: {avg_similarity:.4f}")
        
        return overall_evaluation
    
    def update_system_with_optimized_model(self, model_path: str):
        """
        Mengupdate sistem dengan model yang dioptimalkan
        
        Args:
            model_path: Path ke model yang dioptimalkan
        """
        print("Mengupdate sistem dengan model yang dioptimalkan...")
        
        # Backup model lama
        self.backup_current_model()
        
        # Copy model baru ke lokasi default
        default_model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        shutil.copy2(model_path, default_model_path)
        
        print(f"Model optimal disalin ke lokasi default: {default_model_path}")
        
        # Re-initialize sistem dengan model baru
        print("Menginisialisasi ulang sistem dengan model optimal...")
        
        # Proses data Al-Quran untuk parameter yang dibutuhkan
        dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
        
        # Panggil initialize_fasttext dengan parameter yang diperlukan
        initialize_fasttext(preprocessed_verses)
        
        print("Sistem berhasil diupdate dengan model FastText yang dioptimalkan!")
    
    def run_optimization(self):
        """
        Menjalankan proses optimasi lengkap
        """
        print("=== FastText Model Optimization ===")
        
        # 1. Muat hasil eksperimen untuk mendapatkan konfigurasi optimal
        self.optimal_config = self.load_experiment_results()
        
        # 2. Buat korpus training
        corpus_path = self.create_corpus_from_quran()
        
        try:
            # 3. Latih model dengan parameter optimal
            model_path = self.train_optimized_model(corpus_path)
            
            # 4. Evaluasi model yang dioptimalkan
            evaluation = self.evaluate_optimized_model(model_path)
            
            # 5. Update sistem dengan model baru
            self.update_system_with_optimized_model(model_path)
            
            # 6. Simpan hasil evaluasi
            self._save_evaluation_results(evaluation)
            
            print("\n=== OPTIMASI SELESAI ===")
            print("Model FastText berhasil dioptimalkan dan diintegrasikan ke sistem!")
            
        finally:
            # Bersihkan file temporary
            if os.path.exists(corpus_path):
                os.remove(corpus_path)
                print(f"File temporary dibersihkan: {corpus_path}")
    
    def _save_evaluation_results(self, evaluation: Dict[str, Any]):
        """
        Menyimpan hasil evaluasi ke file
        
        Args:
            evaluation: Hasil evaluasi model
        """
        results_dir = os.path.join(self.base_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        evaluation_file = os.path.join(results_dir, 'fasttext_optimization_evaluation.json')
        
        evaluation_data = {
            'optimization_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'optimal_config': self.optimal_config,
            'evaluation_results': evaluation
        }
        
        with open(evaluation_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        
        print(f"Hasil evaluasi disimpan di: {evaluation_file}")

def main():
    """
    Main function untuk menjalankan optimasi
    """
    print("=== FastText Model Optimization ===")
    
    # Buat optimizer
    optimizer = FastTextOptimizer()
    
    # Jalankan optimasi
    optimizer.run_optimization()
    
    print("\nOptimasi model FastText selesai!")

if __name__ == "__main__":
    import time
    import numpy as np
    main() 