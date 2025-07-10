"""
Script eksperimen untuk membandingkan berbagai metode agregasi FastText
Fase 2: Peningkatan Metode Agregasi
"""

import os
import sys
import json
import time
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.fasttext_model import FastTextModel
from backend.weighted_pooling import FastTextWeightedPooling
from backend.attention_embedding import FastTextAttentionEmbedding
from backend.preprocessing import process_quran_data

class FastTextAggregationExperiment:
    """
    Kelas untuk eksperimen metode agregasi FastText
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, 'results')
        self.models_dir = os.path.join(self.base_dir, 'models/fasttext')
        
        # Buat direktori results jika belum ada
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Metode agregasi yang akan dieksperimen
        self.aggregation_methods = {
            'mean': 'Mean Pooling (Baseline)',
            'tfidf': 'TF-IDF Weighted Pooling',
            'frequency': 'Frequency Weighted Pooling',
            'position': 'Position Weighted Pooling',
            'hybrid': 'Hybrid Weighted Pooling',
            'attention': 'Attention-based Pooling'
        }
        
        # Dataset evaluasi
        self.evaluation_queries = [
            # Query umum
            {'query': 'shalat', 'category': 'umum', 'expected_verses': ['1:1', '2:3', '2:43']},
            {'query': 'puasa', 'category': 'umum', 'expected_verses': ['2:183', '2:184', '2:185']},
            {'query': 'zakat', 'category': 'umum', 'expected_verses': ['2:43', '2:83', '2:110']},
            
            # Query dengan variasi morfologi
            {'query': 'berdoa', 'category': 'morfologi', 'expected_verses': ['2:186', '7:29', '40:60']},
            {'query': 'mendoakan', 'category': 'morfologi', 'expected_verses': ['9:103', '33:56', '48:9']},
            {'query': 'doa', 'category': 'morfologi', 'expected_verses': ['2:186', '7:29', '40:60']},
            
            # Query domain-specific
            {'query': 'malaikat', 'category': 'domain', 'expected_verses': ['2:30', '2:34', '2:98']},
            {'query': 'nabi', 'category': 'domain', 'expected_verses': ['2:136', '3:84', '4:136']},
            {'query': 'rasul', 'category': 'domain', 'expected_verses': ['2:87', '2:101', '2:285']},
            
            # Query dengan kata majemuk
            {'query': 'hari kiamat', 'category': 'majemuk', 'expected_verses': ['2:85', '2:113', '2:174']},
            {'query': 'surga neraka', 'category': 'majemuk', 'expected_verses': ['2:25', '2:39', '2:81']},
            
            # Query dengan kata asing
            {'query': 'alhamdulillah', 'category': 'asing', 'expected_verses': ['1:2', '6:1', '18:1']},
            {'query': 'insyaallah', 'category': 'asing', 'expected_verses': ['2:70', '18:23', '18:24']}
        ]
    
    def load_fasttext_model(self) -> FastTextModel:
        """
        Muat model FastText
        """
        print("Loading FastText model...")
        
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model FastText tidak ditemukan: {model_path}")
        
        model = FastTextModel(model_path=model_path)
        model.load_model()
        
        print("FastText model loaded successfully!")
        return model
    
    def prepare_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Siapkan data ayat untuk eksperimen
        """
        print("Preparing Quran data...")
        
        dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
        
        print(f"Prepared {len(preprocessed_verses)} verses for experiment")
        return preprocessed_verses
    
    def evaluate_method(self, model: FastTextModel, method: str, 
                       preprocessed_verses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluasi metode agregasi tertentu
        
        Args:
            model: Model FastText
            method: Metode agregasi
            preprocessed_verses: Data ayat yang telah diproses
            
        Returns:
            Hasil evaluasi
        """
        print(f"\nEvaluating method: {method}")
        
        start_time = time.time()
        
        # Buat vektor ayat dengan metode tertentu
        if method == 'mean':
            # Baseline: mean pooling
            model.create_verse_vectors(preprocessed_verses)
        
        elif method in ['tfidf', 'frequency', 'position', 'hybrid']:
            # Weighted pooling
            weighted_pooling = FastTextWeightedPooling(model, method)
            weighted_pooling.fit_pooling(preprocessed_verses)
            weighted_pooling.create_verse_vectors_weighted(preprocessed_verses)
        
        elif method == 'attention':
            # Attention-based pooling
            attention_embedding = FastTextAttentionEmbedding(model)
            attention_embedding.create_verse_vectors_attention(preprocessed_verses)
        
        else:
            raise ValueError(f"Method {method} not supported")
        
        # Evaluasi pada semua query
        query_results = []
        for query_info in self.evaluation_queries:
            query = query_info['query']
            expected_verses = query_info['expected_verses']
            category = query_info['category']
            
            metrics = self._evaluate_query(model, query, expected_verses)
            metrics['query'] = query
            metrics['category'] = category
            query_results.append(metrics)
        
        # Hitung rata-rata metrik
        avg_metrics = {
            'method': method,
            'method_name': self.aggregation_methods[method],
            'avg_precision': np.mean([r['precision'] for r in query_results]),
            'avg_recall': np.mean([r['recall'] for r in query_results]),
            'avg_f1': np.mean([r['f1'] for r in query_results]),
            'avg_map': np.mean([r['map'] for r in query_results]),
            'avg_ndcg': np.mean([r['ndcg'] for r in query_results]),
            'execution_time': time.time() - start_time,
            'query_results': query_results
        }
        
        print(f"✅ {method}: F1={avg_metrics['avg_f1']:.3f}, MAP={avg_metrics['avg_map']:.3f}")
        
        return avg_metrics
    
    def _evaluate_query(self, model: FastTextModel, query: str, 
                       expected_verses: List[str]) -> Dict[str, float]:
        """
        Evaluasi query tertentu
        
        Args:
            model: Model FastText
            query: Query untuk dievaluasi
            expected_verses: Daftar ayat yang diharapkan relevan
            
        Returns:
            Metrik evaluasi
        """
        # Lakukan pencarian
        results = model.search(query, limit=20, threshold=0.3)
        
        # Ekstrak verse_id dari hasil
        retrieved_verses = [r['verse_id'] for r in results]
        
        # Hitung metrik
        precision, recall, f1 = self._calculate_precision_recall_f1(
            retrieved_verses, expected_verses
        )
        
        map_score = self._calculate_map(retrieved_verses, expected_verses)
        ndcg_score = self._calculate_ndcg(results, expected_verses)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'map': map_score,
            'ndcg': ndcg_score
        }
    
    def _calculate_precision_recall_f1(self, retrieved: List[str], 
                                      relevant: List[str]) -> Tuple[float, float, float]:
        """
        Hitung precision, recall, dan F1-score
        """
        retrieved_set = set(retrieved)
        relevant_set = set(relevant)
        
        if not retrieved_set:
            return 0.0, 0.0, 0.0
        
        if not relevant_set:
            return 0.0, 0.0, 0.0
        
        # Hitung intersection
        intersection = retrieved_set & relevant_set
        
        precision = len(intersection) / len(retrieved_set)
        recall = len(intersection) / len(relevant_set)
        
        # F1-score
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1
    
    def _calculate_map(self, retrieved: List[str], relevant: List[str]) -> float:
        """
        Hitung Mean Average Precision (MAP)
        """
        if not relevant:
            return 0.0
        
        relevant_set = set(relevant)
        ap_scores = []
        
        # Hitung average precision untuk setiap relevant item
        for relevant_item in relevant_set:
            if relevant_item in retrieved:
                # Posisi item dalam hasil
                position = retrieved.index(relevant_item) + 1
                
                # Precision pada posisi ini
                precision_at_k = 1.0 / position
                ap_scores.append(precision_at_k)
            else:
                ap_scores.append(0.0)
        
        return np.mean(ap_scores)
    
    def _calculate_ndcg(self, results: List[Dict], relevant: List[str]) -> float:
        """
        Hitung Normalized Discounted Cumulative Gain (NDCG)
        """
        if not results:
            return 0.0
        
        relevant_set = set(relevant)
        
        # Hitung DCG
        dcg = 0.0
        for i, result in enumerate(results):
            if result['verse_id'] in relevant_set:
                # Relevance score (1 jika relevan, 0 jika tidak)
                relevance = 1.0
                # Discount factor
                discount = 1.0 / np.log2(i + 2)
                dcg += relevance * discount
        
        # Hitung IDCG (ideal DCG)
        idcg = 0.0
        for i in range(min(len(relevant_set), len(results))):
            relevance = 1.0
            discount = 1.0 / np.log2(i + 2)
            idcg += relevance * discount
        
        # NDCG
        if idcg == 0:
            return 0.0
        else:
            return dcg / idcg
    
    def run_experiment(self) -> Dict[str, Any]:
        """
        Jalankan eksperimen untuk semua metode agregasi
        """
        print("=== FastText Aggregation Experiment ===")
        print(f"Methods to evaluate: {list(self.aggregation_methods.keys())}")
        print(f"Number of queries: {len(self.evaluation_queries)}")
        
        # Siapkan data
        preprocessed_verses = self.prepare_data()
        
        # Muat model
        model = self.load_fasttext_model()
        
        # Jalankan eksperimen untuk setiap metode
        results = {}
        
        for method in self.aggregation_methods.keys():
            try:
                # Reset model untuk setiap metode
                model.verse_vectors = {}
                
                # Evaluasi metode
                method_result = self.evaluate_method(model, method, preprocessed_verses)
                results[method] = method_result
                
            except Exception as e:
                print(f"❌ Error evaluating method {method}: {e}")
                results[method] = {
                    'method': method,
                    'method_name': self.aggregation_methods[method],
                    'error': str(e)
                }
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """
        Simpan hasil eksperimen
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Simpan dalam format JSON
        json_path = os.path.join(self.results_dir, f'fasttext_aggregation_experiment_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Buat ringkasan
        summary = self._create_summary(results)
        summary_path = os.path.join(self.results_dir, f'fasttext_aggregation_summary_{timestamp}.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved:")
        print(f"  - Detailed results: {json_path}")
        print(f"  - Summary: {summary_path}")
        
        return json_path, summary_path
    
    def _create_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buat ringkasan hasil eksperimen
        """
        summary = {
            'experiment_info': {
                'timestamp': datetime.now().isoformat(),
                'methods_evaluated': list(results.keys()),
                'number_of_queries': len(self.evaluation_queries),
                'query_categories': list(set(q['category'] for q in self.evaluation_queries))
            },
            'method_comparison': {},
            'best_methods': {}
        }
        
        # Bandingkan metode
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if valid_results:
            # Ranking berdasarkan F1-score
            f1_ranking = sorted(valid_results.items(), 
                               key=lambda x: x[1]['avg_f1'], reverse=True)
            
            # Ranking berdasarkan MAP
            map_ranking = sorted(valid_results.items(), 
                                key=lambda x: x[1]['avg_map'], reverse=True)
            
            # Ranking berdasarkan NDCG
            ndcg_ranking = sorted(valid_results.items(), 
                                 key=lambda x: x[1]['avg_ndcg'], reverse=True)
            
            summary['method_comparison'] = {
                'f1_ranking': [{'method': m, 'score': r['avg_f1']} for m, r in f1_ranking],
                'map_ranking': [{'method': m, 'score': r['avg_map']} for m, r in map_ranking],
                'ndcg_ranking': [{'method': m, 'score': r['avg_ndcg']} for m, r in ndcg_ranking]
            }
            
            summary['best_methods'] = {
                'best_f1': f1_ranking[0][0],
                'best_map': map_ranking[0][0],
                'best_ndcg': ndcg_ranking[0][0]
            }
        
        return summary
    
    def print_results(self, results: Dict[str, Any]):
        """
        Cetak hasil eksperimen
        """
        print("\n=== EXPERIMENT RESULTS ===")
        
        # Tabel perbandingan
        print(f"\n{'Method':<15} {'F1':<8} {'MAP':<8} {'NDCG':<8} {'Time':<8}")
        print("-" * 50)
        
        for method, result in results.items():
            if 'error' in result:
                print(f"{method:<15} {'ERROR':<8}")
            else:
                print(f"{method:<15} {result['avg_f1']:<8.3f} {result['avg_map']:<8.3f} "
                      f"{result['avg_ndcg']:<8.3f} {result['execution_time']:<8.2f}")
        
        # Best methods
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        if valid_results:
            best_f1 = max(valid_results.items(), key=lambda x: x[1]['avg_f1'])
            best_map = max(valid_results.items(), key=lambda x: x[1]['avg_map'])
            best_ndcg = max(valid_results.items(), key=lambda x: x[1]['avg_ndcg'])
            
            print(f"\n🏆 BEST METHODS:")
            print(f"  Best F1: {best_f1[0]} ({best_f1[1]['avg_f1']:.3f})")
            print(f"  Best MAP: {best_map[0]} ({best_map[1]['avg_map']:.3f})")
            print(f"  Best NDCG: {best_ndcg[0]} ({best_ndcg[1]['avg_ndcg']:.3f})")


def main():
    """
    Main function
    """
    experiment = FastTextAggregationExperiment()
    
    try:
        # Jalankan eksperimen
        results = experiment.run_experiment()
        
        # Simpan hasil
        json_path, summary_path = experiment.save_results(results)
        
        # Cetak hasil
        experiment.print_results(results)
        
        print(f"\n🎉 Experiment completed successfully!")
        print(f"📊 Results saved to: {json_path}")
        print(f"📋 Summary saved to: {summary_path}")
        
    except Exception as e:
        print(f"❌ Error during experiment: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 