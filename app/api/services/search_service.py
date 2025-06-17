"""
Search service implementation.
"""
from typing import List, Dict, Optional
from backend.db import get_db_connection, add_search_history, update_app_statistics
from backend.lexical_search import LexicalSearch
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
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
    
    def _init_semantic_model(self, model_type: str):
        """Initialize semantic model if not initialized."""
        if model_type not in self._semantic_models:
            try:
                # Gunakan path yang relatif terhadap root project (folder semantic)
                # Naik 3 levels dari app/api/services/search_service.py ke folder semantic
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                print(f"Root directory: {root_dir}")  # Debug: tampilkan root directory
                
                if model_type == 'word2vec':
                    model_path = os.path.join(root_dir, 'models', 'idwiki_word2vec', 'idwiki_word2vec_200_new_lower.model')
                    vectors_path = os.path.join(root_dir, 'database', 'vectors', 'word2vec_verses.pkl')
                    
                    # Debug: tampilkan path lengkap
                    print(f"Model path: {model_path}")
                    print(f"Vectors path: {vectors_path}")
                    
                    # Periksa keberadaan file model dan vektor
                    if not os.path.exists(model_path):
                        raise ValueError(f"File model Word2Vec tidak ditemukan di {model_path}")
                    if not os.path.exists(vectors_path):
                        raise ValueError(f"File vektor ayat Word2Vec tidak ditemukan di {vectors_path}")
                    
                    # Inisialisasi model
                    self._semantic_models[model_type] = Word2VecModel(model_path=model_path)
                    
                    # Muat model dan vektor ayat
                    print(f"Memuat model Word2Vec dari {model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {vectors_path}...")
                    self._semantic_models[model_type].load_verse_vectors(vectors_path)
                    print("Model Word2Vec berhasil dimuat!")
                        
                elif model_type == 'fasttext':
                    model_path = os.path.join(root_dir, 'models', 'fasttext', 'fasttext_model.model')
                    vectors_path = os.path.join(root_dir, 'database', 'vectors', 'fasttext_verses.pkl')
                    
                    # Debug: tampilkan path lengkap
                    print(f"Model path: {model_path}")
                    print(f"Vectors path: {vectors_path}")
                    
                    # Periksa keberadaan file model dan vektor
                    if not os.path.exists(model_path):
                        raise ValueError(f"File model FastText tidak ditemukan di {model_path}")
                    if not os.path.exists(vectors_path):
                        raise ValueError(f"File vektor ayat FastText tidak ditemukan di {vectors_path}")
                    
                    # Inisialisasi model
                    self._semantic_models[model_type] = FastTextModel(model_path=model_path)
                    
                    # Muat model dan vektor ayat
                    print(f"Memuat model FastText dari {model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {vectors_path}...")
                    self._semantic_models[model_type].load_verse_vectors(vectors_path)
                    print("Model FastText berhasil dimuat!")
                        
                elif model_type == 'glove':
                    model_path = os.path.join(root_dir, 'models', 'glove', 'alquran_vectors.txt')
                    vectors_path = os.path.join(root_dir, 'database', 'vectors', 'glove_verses.pkl')
                    
                    # Debug: tampilkan path lengkap
                    print(f"Model path: {model_path}")
                    print(f"Vectors path: {vectors_path}")
                    
                    # Periksa keberadaan file model dan vektor
                    if not os.path.exists(model_path):
                        raise ValueError(f"File model GloVe tidak ditemukan di {model_path}")
                    if not os.path.exists(vectors_path):
                        raise ValueError(f"File vektor ayat GloVe tidak ditemukan di {vectors_path}")
                    
                    # Inisialisasi model
                    self._semantic_models[model_type] = GloVeModel(model_path=model_path)
                    
                    # Muat model dan vektor ayat
                    print(f"Memuat model GloVe dari {model_path}...")
                    self._semantic_models[model_type].load_model()
                    print(f"Memuat vektor ayat dari {vectors_path}...")
                    self._semantic_models[model_type].load_verse_vectors(vectors_path)
                    print("Model GloVe berhasil dimuat!")
                        
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
                       threshold: float = 0.5, user_id: Optional[int] = None) -> Dict:
        """Perform semantic search."""
        try:
            self._init_semantic_model(model_type)
            model = self._semantic_models[model_type]
            
            results = model.search(query, language, limit, threshold)
            results = self._enhance_results_with_classification(results)
            
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