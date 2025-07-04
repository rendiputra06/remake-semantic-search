"""
Search service implementation.
"""
from typing import List, Dict, Optional
from backend.db import get_db_connection, add_search_history, update_app_statistics
from backend.lexical_search import LexicalSearch
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
from backend.ensemble_embedding import EnsembleEmbeddingModel
import json
import os

class SearchService:
    """Service class for handling search operations."""
    
    def __init__(self):
        self._lexical_search = None
        self._semantic_models = {}
    
    def _init_lexical_search(self):
        """Initialize lexical search if not initialized."""
        if not self._lexical_search:
            self._lexical_search = LexicalSearch()
            try:
                self._lexical_search.load_index()
            except Exception as e:
                print(f"Error loading lexical index: {e}")
                raise
    
    def _init_and_load_model(self, model_key, model_class):
        if model_key not in self._semantic_models:
            print(f"[DEBUG] Inisialisasi {model_key} dengan default path dari kelas model.")
            model = model_class()
            model.load_model()
            model.load_verse_vectors()
            self._semantic_models[model_key] = model
    
    def _init_semantic_model(self, model_type: str):
        """Initialize semantic model if not initialized."""
        if model_type not in self._semantic_models:
            try:
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                print(f"Root directory: {root_dir}")  # Debug: tampilkan root directory
                
                if model_type == 'word2vec':
                    # Inisialisasi model
                    self._semantic_models[model_type] = Word2VecModel()
                    print(f"Memuat model Word2Vec dari {self._semantic_models[model_type].model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {self._semantic_models[model_type].verse_vectors}...")
                    self._semantic_models[model_type].load_verse_vectors()
                    print("Model Word2Vec berhasil dimuat!")
                        
                elif model_type == 'fasttext':
                    self._semantic_models[model_type] = FastTextModel()
                    print(f"Memuat model FastText dari {self._semantic_models[model_type].model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {self._semantic_models[model_type].verse_vectors}...")
                    self._semantic_models[model_type].load_verse_vectors()
                    print("Model FastText berhasil dimuat!")
                        
                elif model_type == 'glove':
                    self._semantic_models[model_type] = GloVeModel()
                    print(f"Memuat model GloVe dari {self._semantic_models[model_type].model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {self._semantic_models[model_type].verse_vectors}...")
                    self._semantic_models[model_type].load_verse_vectors()
                    print("Model GloVe berhasil dimuat!")
                        
                elif model_type == 'ensemble':
                    # Inisialisasi model-model dasar jika belum
                    self._init_and_load_model('word2vec', Word2VecModel)
                    self._init_and_load_model('fasttext', FastTextModel)
                    self._init_and_load_model('glove', GloVeModel)
                    # Inisialisasi ensemble
                    ensemble = EnsembleEmbeddingModel(
                        self._semantic_models['word2vec'],
                        self._semantic_models['fasttext'],
                        self._semantic_models['glove']
                    )
                    ensemble.load_models()
                    ensemble.load_verse_vectors()
                    self._semantic_models[model_type] = ensemble
                else:
                    raise ValueError(f"Tipe model tidak didukung: {model_type}")
                    
            except Exception as e:
                print(f"Error initializing {model_type} model: {e}")
                raise
    
    def _enhance_results_with_classification(self, results: List[Dict]) -> List[Dict]:
        """Add classification information to search results."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, list_ayat 
            FROM quran_index 
            WHERE list_ayat IS NOT NULL
        ''')
        
        indexes_with_ayat = cursor.fetchall()
        conn.close()
        
        for result in results:
            surah = result['surah_number']
            ayat = result['ayat_number']
            ayat_ref = f"{surah}:{ayat}"
            
            matching_indexes = []
            for idx in indexes_with_ayat:
                if idx['list_ayat']:
                    try:
                        ayat_list = json.loads(idx['list_ayat'])
                        if ayat_list and ayat_ref in ayat_list:
                            matching_indexes.append({
                                'id': idx['id'],
                                'title': idx['title']
                            })
                    except json.JSONDecodeError:
                        continue
            
            if matching_indexes:
                primary_classification = matching_indexes[0]
                result['classification'] = {
                    'id': primary_classification['id'],
                    'title': primary_classification['title'],
                    'path': self._get_classification_path(primary_classification['id'])
                }
                result['related_classifications'] = matching_indexes
            else:
                result['classification'] = None
                result['related_classifications'] = []
        
        return results
    
    def _get_classification_path(self, index_id: int) -> List[str]:
        """Get classification path for an index."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        path = []
        current_id = index_id
        
        while current_id:
            cursor.execute('SELECT title, parent_id FROM quran_index WHERE id = ?', (current_id,))
            result = cursor.fetchone()
            if result:
                path.insert(0, result['title'])
                current_id = result['parent_id']
            else:
                break
        
        conn.close()
        return path
    
    def semantic_search(self, query: str, model_type: str = 'word2vec', 
                       language: str = 'id', limit: int = 10, 
                       threshold: float = 0.5, user_id: Optional[int] = None,
                       trace: Optional[dict] = None) -> Dict:
        """Perform semantic search. Mendukung tracing jika trace dict diberikan."""
        try:
            if trace is not None:
                trace.setdefault('steps', []).append({'step': 'init_model', 'data': {'model_type': model_type}})
                trace.setdefault('logs', []).append(f'Inisialisasi model: {model_type}')
            self._init_semantic_model(model_type)
            model = self._semantic_models[model_type]

            if trace is not None:
                trace['steps'].append({'step': 'embedding', 'data': {'query': query}})
                trace['logs'].append(f'Proses embedding untuk query: {query}')

            results = model.search(query, language, limit, threshold)

            if trace is not None:
                trace['steps'].append({'step': 'similarity', 'data': {'result_count': len(results)}})
                trace['logs'].append(f'Perhitungan similarity selesai, hasil: {len(results)} ayat')

            results = self._enhance_results_with_classification(results)

            if trace is not None:
                trace['steps'].append({'step': 'ranking', 'data': {'result_count': len(results)}})
                trace['logs'].append('Ranking dan klasifikasi hasil selesai')

            if user_id:
                add_search_history(user_id, query, model_type, len(results))
                update_app_statistics(
                    searches=1,
                    users=1,
                    model=model_type,
                    avg_results=len(results)
                )

            return {
                'query': query,
                'model': model_type,
                'results': results,
                'count': len(results)
            }
        except Exception as e:
            if trace is not None:
                trace['logs'].append(f'Error: {str(e)}')
            raise Exception(f'Error saat melakukan pencarian: {str(e)}')
    
    def lexical_search(self, query: str, exact_match: bool = False,
                      use_regex: bool = False, limit: int = 10,
                      user_id: Optional[int] = None) -> Dict:
        """Perform lexical search."""
        try:
            self._init_lexical_search()
            
            results = self._lexical_search.search(query, exact_match, use_regex, limit)
            results = self._enhance_results_with_classification(results)
            
            if user_id:
                add_search_history(user_id, query, 'lexical', len(results))
            
            return {
                'success': True,
                'data': {
                    'query': query,
                    'search_type': 'lexical',
                    'exact_match': exact_match,
                    'use_regex': use_regex,
                    'results': results,
                    'count': len(results)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat melakukan pencarian: {str(e)}'
            }
    
    def get_search_distribution(self, results: List[Dict]) -> List[Dict]:
        """Get distribution of search results by classification."""
        classification_counts = {}
        
        for result in results:
            if 'classification' in result and result['classification']:
                classification_id = result['classification']['id']
                classification_title = result['classification']['title']
                
                if classification_id in classification_counts:
                    classification_counts[classification_id]['count'] += 1
                else:
                    classification_counts[classification_id] = {
                        'category': classification_title,
                        'count': 1
                    }
        
        distribution = list(classification_counts.values())
        distribution.sort(key=lambda x: x['count'], reverse=True)
        
        return distribution