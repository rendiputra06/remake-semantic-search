"""
Script untuk mengupdate FastText model dengan metode agregasi optimal
Fase 2: Peningkatan Metode Agregasi
"""

import os
import sys
import json
import time
import pickle
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.fasttext_model import FastTextModel
from backend.weighted_pooling import FastTextWeightedPooling
from backend.attention_embedding import FastTextAttentionEmbedding
from backend.preprocessing import process_quran_data

class FastTextAggregationOptimizer:
    """
    Kelas untuk mengoptimalkan FastText model dengan metode agregasi terbaik
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, 'results')
        self.models_dir = os.path.join(self.base_dir, 'models/fasttext')
        self.backup_dir = os.path.join(self.base_dir, 'models/fasttext/backup')
        
        # Buat direktori backup jika belum ada
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def load_experiment_results(self) -> Dict[str, Any]:
        """
        Muat hasil eksperimen agregasi
        """
        print("Loading aggregation experiment results...")
        
        # Cari file hasil eksperimen terbaru
        experiment_files = []
        for filename in os.listdir(self.results_dir):
            if filename.startswith('fasttext_aggregation_experiment_') and filename.endswith('.json'):
                experiment_files.append(filename)
        
        if not experiment_files:
            raise FileNotFoundError("Tidak ada file hasil eksperimen agregasi yang ditemukan")
        
        # Ambil file terbaru
        latest_file = max(experiment_files)
        filepath = os.path.join(self.results_dir, latest_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"Loaded results from: {filepath}")
        return results
    
    def find_optimal_method(self, results: Dict[str, Any]) -> str:
        """
        Temukan metode agregasi optimal berdasarkan hasil eksperimen
        
        Args:
            results: Hasil eksperimen agregasi
            
        Returns:
            Metode optimal
        """
        # Filter hasil yang valid (tidak ada error)
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if not valid_results:
            raise ValueError("Tidak ada hasil valid dari eksperimen")
        
        # Ranking berdasarkan F1-score (metrik utama)
        f1_ranking = sorted(valid_results.items(), 
                           key=lambda x: x[1]['avg_f1'], reverse=True)
        
        optimal_method = f1_ranking[0][0]
        optimal_score = f1_ranking[0][1]['avg_f1']
        
        print(f"🏆 Optimal method: {optimal_method} (F1-score: {optimal_score:.3f})")
        
        # Tampilkan ranking lengkap
        print("\n📊 Method Ranking (F1-score):")
        for i, (method, result) in enumerate(f1_ranking):
            print(f"  {i+1}. {method}: {result['avg_f1']:.3f}")
        
        return optimal_method
    
    def backup_current_model(self):
        """
        Backup model FastText saat ini
        """
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        if os.path.exists(model_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f'fasttext_backup_{timestamp}.model')
            
            import shutil
            shutil.copy2(model_path, backup_path)
            print(f"📦 Model dibackup ke: {backup_path}")
            return backup_path
        return None
    
    def create_optimized_model(self, optimal_method: str, 
                              preprocessed_verses: Dict[str, Dict[str, Any]]) -> FastTextModel:
        """
        Buat model FastText yang dioptimalkan dengan metode agregasi terbaik
        
        Args:
            optimal_method: Metode agregasi optimal
            preprocessed_verses: Data ayat yang telah diproses
            
        Returns:
            Model FastText yang dioptimalkan
        """
        print(f"🔄 Creating optimized model with {optimal_method} aggregation...")
        
        # Muat model FastText
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model FastText tidak ditemukan: {model_path}")
        
        model = FastTextModel(model_path=model_path)
        model.load_model()
        
        # Buat vektor ayat dengan metode optimal
        if optimal_method == 'mean':
            # Baseline: mean pooling
            model.create_verse_vectors(preprocessed_verses)
            
        elif optimal_method in ['tfidf', 'frequency', 'position', 'hybrid']:
            # Weighted pooling
            weighted_pooling = FastTextWeightedPooling(model, optimal_method)
            weighted_pooling.fit_pooling(preprocessed_verses)
            weighted_pooling.create_verse_vectors_weighted(preprocessed_verses)
            
            # Simpan model weighted pooling
            pooling_model_path = os.path.join(self.models_dir, f'weighted_pooling_{optimal_method}.pkl')
            weighted_pooling.save_pooling_model(pooling_model_path)
            print(f"💾 Weighted pooling model disimpan: {pooling_model_path}")
            
        elif optimal_method == 'attention':
            # Attention-based pooling
            attention_embedding = FastTextAttentionEmbedding(model)
            attention_embedding.create_verse_vectors_attention(preprocessed_verses)
            
            # Simpan model attention
            attention_model_path = os.path.join(self.models_dir, 'attention_model.pkl')
            attention_embedding.save_attention_model(attention_model_path)
            print(f"💾 Attention model disimpan: {attention_model_path}")
            
        else:
            raise ValueError(f"Method {optimal_method} not supported")
        
        print(f"✅ Model optimized with {optimal_method} aggregation")
        return model
    
    def save_optimized_model(self, model: FastTextModel, optimal_method: str):
        """
        Simpan model yang dioptimalkan
        """
        # Simpan vektor ayat yang dioptimalkan
        optimized_vector_path = os.path.join(self.base_dir, 'database/vectors/fasttext_optimized_verses.pkl')
        os.makedirs(os.path.dirname(optimized_vector_path), exist_ok=True)
        
        data_to_save = {
            'verse_vectors': model.verse_vectors,
            'verse_data': model.verse_data,
            'aggregation_method': optimal_method,
            'optimization_timestamp': datetime.now().isoformat()
        }
        
        with open(optimized_vector_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        
        print(f"💾 Optimized vectors disimpan: {optimized_vector_path}")
        
        # Simpan informasi optimasi
        optimization_info = {
            'optimal_method': optimal_method,
            'optimization_timestamp': datetime.now().isoformat(),
            'vector_count': len(model.verse_vectors),
            'vector_dimension': model.model.vector_size if model.model else None
        }
        
        info_path = os.path.join(self.models_dir, 'optimization_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_info, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Optimization info disimpan: {info_path}")
    
    def evaluate_optimized_model(self, model: FastTextModel, 
                                original_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluasi model yang dioptimalkan
        
        Args:
            model: Model yang dioptimalkan
            original_results: Hasil eksperimen asli
            
        Returns:
            Hasil evaluasi
        """
        print("Evaluating optimized model...")
        
        # Ambil optimal method dari original results
        optimal_method = None
        for method, result in original_results.items():
            if 'error' not in result:
                optimal_method = method
                break
        
        if not optimal_method:
            raise ValueError("Tidak dapat menemukan metode optimal")
        
        # Test beberapa query
        test_queries = ['shalat', 'puasa', 'malaikat', 'berdoa']
        
        evaluation_results = {
            'optimal_method': optimal_method,
            'test_queries': {},
            'model_info': {
                'vector_count': len(model.verse_vectors),
                'vector_dimension': model.model.vector_size if model.model else None
            }
        }
        
        for query in test_queries:
            try:
                results = model.search(query, limit=10, threshold=0.3)
                evaluation_results['test_queries'][query] = {
                    'result_count': len(results),
                    'top_similarity': results[0]['similarity'] if results else 0.0,
                    'avg_similarity': np.mean([r['similarity'] for r in results]) if results else 0.0
                }
            except Exception as e:
                evaluation_results['test_queries'][query] = {'error': str(e)}
        
        return evaluation_results
    
    def update_system_integration(self, optimal_method: str):
        """
        Update integrasi sistem dengan metode agregasi optimal
        """
        print("Updating system integration...")
        
        # Update file konfigurasi atau dokumentasi
        integration_info = {
            'fasttext_aggregation_method': optimal_method,
            'update_timestamp': datetime.now().isoformat(),
            'phase': '2',
            'description': 'FastText model optimized with best aggregation method'
        }
        
        # Simpan informasi integrasi
        integration_path = os.path.join(self.models_dir, 'system_integration.json')
        with open(integration_path, 'w', encoding='utf-8') as f:
            json.dump(integration_info, f, indent=2, ensure_ascii=False)
        
        print(f"💾 System integration info disimpan: {integration_path}")
    
    def optimize_model(self) -> bool:
        """
        Proses utama optimasi model FastText
        """
        print("=== FastText Aggregation Optimization ===")
        
        try:
            # 1. Muat hasil eksperimen
            results = self.load_experiment_results()
            
            # 2. Temukan metode optimal
            optimal_method = self.find_optimal_method(results)
            
            # 3. Backup model saat ini
            backup_path = self.backup_current_model()
            
            # 4. Siapkan data
            print("Preparing Quran data...")
            dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
            preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
            
            # 5. Buat model yang dioptimalkan
            optimized_model = self.create_optimized_model(optimal_method, preprocessed_verses)
            
            # 6. Simpan model yang dioptimalkan
            self.save_optimized_model(optimized_model, optimal_method)
            
            # 7. Evaluasi model yang dioptimalkan
            evaluation = self.evaluate_optimized_model(optimized_model, results)
            
            # 8. Update integrasi sistem
            self.update_system_integration(optimal_method)
            
            # 9. Simpan hasil evaluasi
            evaluation_path = os.path.join(self.results_dir, f'optimization_evaluation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(evaluation_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation, f, indent=2, ensure_ascii=False)
            
            print(f"\n🎉 Optimization completed successfully!")
            print(f"📊 Evaluation saved: {evaluation_path}")
            print(f"🏆 Optimal method: {optimal_method}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during optimization: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Main function
    """
    optimizer = FastTextAggregationOptimizer()
    
    success = optimizer.optimize_model()
    
    if success:
        print("\n✅ FastText model optimization completed!")
        print("🚀 Model ready for production use")
    else:
        print("\n❌ FastText model optimization failed!")
        print("🔧 Please check the error messages above")


if __name__ == "__main__":
    main() 