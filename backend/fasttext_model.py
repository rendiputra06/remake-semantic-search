"""
Modul untuk menggunakan model FastText dalam pencarian semantik
"""
import os
import pickle
import numpy as np
from gensim.models import FastText
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import json

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

class FastTextModel:
    """
    Kelas untuk menangani model FastText
    """
    def __init__(self, model_path: str = None, vector_path: str = None, aggregation_method: str = None):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        if model_path is None:
            model_path = os.path.join(base_dir, '../models/fasttext/fasttext_model.model')
        if vector_path is None:
            vector_path = os.path.join(base_dir, '../database/vectors/fasttext_verses.pkl')
        self.model_path = os.path.abspath(model_path)
        self.vector_path = os.path.abspath(vector_path)
        self.model = None
        self.verse_vectors = {}
        self.verse_data = {}
        # Auto-load aggregation_method from config if not provided
        if aggregation_method is None:
            config_path = os.path.join(base_dir, '../models/fasttext/system_integration.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.aggregation_method = config.get('fasttext_aggregation_method', 'mean')
            except Exception:
                self.aggregation_method = 'mean'
        else:
            self.aggregation_method = aggregation_method
    
    def load_model(self) -> None:
        """
        Memuat model FastText dari file
        """
        try:
            print(f"Loading FastText model from {self.model_path}...")
            
            # Load model FastText
            self.model = FastText.load(self.model_path)
            print("Model FastText loaded successfully!")
            
            # Verifikasi bahwa model dimuat dengan benar
            if not hasattr(self.model, 'wv'):
                raise TypeError("Model yang dimuat tidak memiliki atribut wv")
                
        except Exception as e:
            print(f"Error loading model: {e}")
            raise e
    
    def create_verse_vectors(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membuat vektor untuk setiap ayat Al-Quran
        """
        if self.model is None:
            raise ValueError("Model belum dimuat. Jalankan load_model() terlebih dahulu.")
        
        print("Creating verse vectors with FastText...")
        
        # Simpan data ayat untuk referensi
        self.verse_data = preprocessed_verses
        
        # Buat vektor untuk setiap ayat
        for verse_id, verse_info in preprocessed_verses.items():
            tokens = verse_info['tokens']
            # Hitung vektor ayat sebagai rata-rata vektor kata
            verse_vector = self._calculate_verse_vector(tokens)
            if verse_vector is not None:
                self.verse_vectors[verse_id] = verse_vector
        
        print(f"Created vectors for {len(self.verse_vectors)} verses using FastText")
    
    def _calculate_verse_vector(self, tokens: List[str]) -> np.ndarray:
        """
        Menghitung vektor untuk sebuah ayat berdasarkan token-tokennya
        """
        if not tokens:
            return None
        
        # Kumpulkan vektor untuk setiap kata
        token_vectors = []
        for token in tokens:
            try:
                # Keuntungan FastText: dapat menangani out-of-vocabulary words
                vector = self.model.wv[token]
                token_vectors.append(vector)
            except Exception as e:
                print(f"Error getting vector for token '{token}': {e}")
                continue
        
        # Jika tidak ada kata yang ditemukan dalam model, kembalikan None
        if not token_vectors:
            return None
        
        # Hitung rata-rata vektor
        verse_vector = np.mean(token_vectors, axis=0)
        return l2_normalize(verse_vector)
    
    def search(self, query: str, language: str = 'id', limit: int = 10, threshold: float = 0.5, aggregation_method: str = None, vector_path: str = None) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian semantik berdasarkan query
        aggregation_method: 'mean', 'tfidf', 'hybrid', 'attention', etc.
        vector_path: path ke file vektor ayat (opsional)
        """
        # Jika user ingin override file vektor
        if vector_path is not None and os.path.exists(vector_path):
            self.load_verse_vectors(vector_path)
        # Jika user ingin override metode agregasi
        method = aggregation_method or self.aggregation_method
        # Jika file vektor yang dimuat tidak sesuai dengan metode, bisa tambahkan log warning di sini
        if self.model is None:
            raise ValueError("Model belum dimuat. Jalankan load_model() terlebih dahulu.")
        if not self.verse_vectors:
            raise ValueError("Vektor ayat belum dibuat. Jalankan create_verse_vectors() terlebih dahulu.")
        # Praproses query
        from backend.preprocessing import preprocess_text
        query_tokens = preprocess_text(query)
        # Hitung vektor query sesuai metode agregasi
        if method == 'mean' or method is None:
            query_vector = self._calculate_verse_vector(query_tokens)
        elif method in ['tfidf', 'frequency', 'position', 'hybrid']:
            from backend.weighted_pooling import WeightedPooling
            pooling = WeightedPooling(method=method)
            # Fit pooling dengan data ayat (jika perlu, bisa cache)
            pooling.fit([v['tokens'] for v in self.verse_data.values()], [v['translation'] for v in self.verse_data.values()])
            token_vectors = []
            valid_tokens = []
            for token in query_tokens:
                try:
                    vector = self.model.wv[token]
                    token_vectors.append(vector)
                    valid_tokens.append(token)
                except Exception:
                    continue
            if not token_vectors:
                query_vector = None
            else:
                query_vector = pooling.aggregate_vectors(token_vectors, valid_tokens)
                query_vector = l2_normalize(query_vector)
        elif method == 'attention':
            from backend.attention_embedding import SelfAttention
            if self.model is None:
                raise ValueError("Model belum dimuat.")
            vector_dim = self.model.vector_size
            attention = SelfAttention(vector_dim, attention_dim=64)
            token_vectors = []
            for token in query_tokens:
                try:
                    vector = self.model.wv[token]
                    token_vectors.append(vector)
                except Exception:
                    continue
            if not token_vectors:
                query_vector = None
            else:
                _, weighted_vectors = attention.compute_attention(token_vectors)
                query_vector = np.mean(weighted_vectors, axis=0)
                query_vector = l2_normalize(query_vector)
        else:
            # Default fallback
            query_vector = self._calculate_verse_vector(query_tokens)
        if query_vector is None:
            return []
        # Hitung kesamaan kosinus dengan semua ayat
        similarities = []
        for verse_id, verse_vector in self.verse_vectors.items():
            similarity = float(cosine_similarity([query_vector], [verse_vector])[0][0])
            similarities.append((verse_id, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        # Ambil hasil sebanyak limit
        if limit is not None:
            top_results = similarities[:int(limit)]
        else:
            top_results = similarities[:]
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
        sim_scores = [r['similarity'] for r in results]
        use_threshold = threshold
        if threshold is None:
            use_threshold = calculate_adaptive_threshold(sim_scores, fallback=0.5)
        filtered_results = [r for r in results if r['similarity'] >= use_threshold]
        return filtered_results
    
    def save_verse_vectors(self, output_path: str = '../database/vectors/fasttext_verses.pkl') -> None:
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
        
        print(f"FastText verse vectors saved to {output_path}")
    
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
            print(f"Loaded vectors for {len(self.verse_vectors)} verses from {input_path} using FastText")
        except Exception as e:
            print(f"Error loading verse vectors: {e}")
            raise e
    
    def print_model_info(self):
        print("==== FastTextModel Info ====")
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