"""
Modul untuk menggunakan model Word2Vec dalam pencarian semantik
"""
import os
import pickle
import numpy as np
from gensim.models import Word2Vec, KeyedVectors
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity

def l2_normalize(vec):
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def calculate_adaptive_threshold(scores, fallback=0.5):
    if not scores:
        return fallback
    try:
        perc = np.percentile(scores, 75)
        if np.isnan(perc) or perc == 0:
            return fallback
        return perc
    except Exception:
        return fallback

class Word2VecModel:
    """
    Kelas untuk menangani model Word2Vec
    """
    def __init__(self, model_path: str = None, vector_path: str = None):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        if model_path is None:
            model_path = os.path.join(base_dir, '../models/idwiki_word2vec/idwiki_word2vec_200_new_lower.model')
        if vector_path is None:
            vector_path = os.path.join(base_dir, '../database/vectors/word2vec_verses.pkl')
        self.model_path = os.path.abspath(model_path)
        self.vector_path = os.path.abspath(vector_path)
        self.model = None
        self.verse_vectors = {}
        self.verse_data = {}
    
    def load_model(self) -> None:
        """
        Memuat model Word2Vec dari file
        """
        try:
            print(f"Loading Word2Vec model from {self.model_path}...")
            
            # Coba load sebagai KeyedVectors terlebih dahulu
            try:
                self.model = KeyedVectors.load(self.model_path)
                print("Model loaded successfully as KeyedVectors!")
            except Exception as e:
                print(f"Could not load as KeyedVectors: {e}")
                
                # Coba load sebagai model Word2Vec penuh
                try:
                    full_model = Word2Vec.load(self.model_path)
                    # Ambil word vectors saja dari model penuh
                    if hasattr(full_model, 'wv'):
                        self.model = full_model.wv
                        print("Model loaded successfully as Word2Vec and converted to word vectors!")
                    else:
                        raise ValueError("Loaded Word2Vec model doesn't have word vectors (wv) attribute")
                except Exception as e2:
                    # Coba load dengan format lain
                    try:
                        self.model = KeyedVectors.load_word2vec_format(self.model_path, binary=True)
                        print("Model loaded successfully in word2vec format!")
                    except Exception as e3:
                        raise ValueError(f"Failed to load model in any format: {e}, {e2}, {e3}")
            
            # Verifikasi bahwa model adalah KeyedVectors atau memiliki atribut yang diperlukan
            if not (isinstance(self.model, KeyedVectors) or hasattr(self.model, 'wv')):
                raise TypeError("Model yang dimuat bukan KeyedVectors dan tidak memiliki atribut wv")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e
    
    def create_verse_vectors(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membuat vektor untuk setiap ayat Al-Quran
        """
        if self.model is None:
            raise ValueError("Model belum dimuat. Jalankan load_model() terlebih dahulu.")
        
        print("Creating verse vectors...")
        
        # Simpan data ayat untuk referensi
        self.verse_data = preprocessed_verses
        
        # Buat vektor untuk setiap ayat
        for verse_id, verse_info in preprocessed_verses.items():
            tokens = verse_info['tokens']
            # Hitung vektor ayat sebagai rata-rata vektor kata
            verse_vector = self._calculate_verse_vector(tokens)
            if verse_vector is not None:
                self.verse_vectors[verse_id] = verse_vector
        
        print(f"Created vectors for {len(self.verse_vectors)} verses")
    
    def _calculate_verse_vector(self, tokens: List[str]) -> np.ndarray:
        """
        Menghitung vektor untuk sebuah ayat berdasarkan token-tokennya
        """
        if not tokens:
            return None
        
        # Kumpulkan vektor untuk setiap kata yang ada dalam model
        token_vectors = []
        for token in tokens:
            try:
                # Periksa apakah self.model adalah KeyedVectors atau memiliki atribut key_to_index
                if hasattr(self.model, 'key_to_index') and token in self.model.key_to_index:
                    token_vectors.append(self.model[token])
                # Jika tidak, coba akses vektor secara langsung dengan aman
                elif hasattr(self.model, 'wv'):
                    # Jika model adalah Word2Vec penuh, gunakan wv
                    if token in self.model.wv:
                        token_vectors.append(self.model.wv[token])
                else:
                    # Coba cara tradisional dengan try/except
                    try:
                        vector = self.model[token]
                        token_vectors.append(vector)
                    except:
                        pass
            except Exception as e:
                print(f"Error getting vector for token '{token}': {e}")
                continue
        
        # Jika tidak ada kata yang ditemukan dalam model, kembalikan None
        if not token_vectors:
            return None
        
        # Hitung rata-rata vektor
        verse_vector = np.mean(token_vectors, axis=0)
        return l2_normalize(verse_vector)
    
    def search(self, query: str, language: str = 'id', limit: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian semantik berdasarkan query
        """
        if self.model is None:
            raise ValueError("Model belum dimuat. Jalankan load_model() terlebih dahulu.")
        
        if not self.verse_vectors:
            raise ValueError("Vektor ayat belum dibuat. Jalankan create_verse_vectors() terlebih dahulu.")
        
        # Praproses query
        from backend.preprocessing import preprocess_text
        query_tokens = preprocess_text(query)
        
        # Hitung vektor query
        query_vector = self._calculate_verse_vector(query_tokens)
        if query_vector is None:
            return []
        
        # Hitung kesamaan kosinus dengan semua ayat
        similarities = []
        for verse_id, verse_vector in self.verse_vectors.items():
            similarity = float(cosine_similarity([query_vector], [verse_vector])[0][0])
            similarities.append((verse_id, similarity))
        
        # Urutkan hasil berdasarkan kesamaan
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Ambil hasil sebanyak limit
        top_results = similarities[:limit]
        
        # Format hasil
        results = []
        for verse_id, similarity in top_results:
            verse_info = self.verse_data[verse_id]
            results.append({
                'verse_id': verse_id,
                'surah_number': verse_info['surah_number'],
                'surah_name': verse_info['surah_name'],
                'ayat_number': verse_info['ayat_number'],
                'arabic': verse_info['arabic'],
                'translation': verse_info['translation'],
                'similarity': similarity
            })
        
        # Threshold adaptif jika threshold=None
        sim_scores = [r['similarity'] for r in results]
        use_threshold = threshold
        if threshold is None:
            use_threshold = calculate_adaptive_threshold(sim_scores, fallback=0.5)
        filtered_results = [r for r in results if r['similarity'] >= use_threshold]
        return filtered_results
    
    def save_verse_vectors(self, output_path: str = '../database/vectors/word2vec_verses.pkl') -> None:
        """
        Menyimpan vektor ayat ke file
        """
        if not self.verse_vectors:
            raise ValueError("Vektor ayat belum dibuat.")
        
        # Pastikan direktori ada
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Simpan vektor dan data ayat
        data_to_save = {
            'verse_vectors': self.verse_vectors,
            'verse_data': self.verse_data
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        
        print(f"Verse vectors saved to {output_path}")
    
    def load_verse_vectors(self, input_path: str = None) -> None:
        """
        Memuat vektor ayat dari file
        """
        if input_path is None:
            input_path = self.vector_path
        try:
            with open(input_path, 'rb') as f:
                data = pickle.load(f)
            self.verse_vectors = data['verse_vectors']
            self.verse_data = data['verse_data']
            print(f"Loaded vectors for {len(self.verse_vectors)} verses from {input_path}")
        except Exception as e:
            print(f"Error loading verse vectors: {e}")
            raise e
    
    def print_model_info(self):
        print("==== Word2VecModel Info ====")
        print(f"Model path: {self.model_path}")
        print(f"Vector path: {self.vector_path}")
        print(f"Model loaded: {'Yes' if self.model is not None else 'No'}")
        print(f"Verse vectors loaded: {len(self.verse_vectors)} ayat")
        if self.verse_vectors:
            first_vec = next(iter(self.verse_vectors.values()))
            print(f"Vector dimension: {first_vec.shape if hasattr(first_vec, 'shape') else type(first_vec)}")
        else:
            print("Vector dimension: -")
        print("============================") 