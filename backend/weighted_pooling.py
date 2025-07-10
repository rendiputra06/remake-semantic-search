"""
Modul untuk implementasi berbagai metode weighted pooling
Meningkatkan metode agregasi vektor kata menjadi vektor ayat
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import pickle
import os

class WeightedPooling:
    """
    Kelas untuk implementasi berbagai metode weighted pooling
    """
    
    def __init__(self, method: str = 'tfidf'):
        """
        Inisialisasi weighted pooling
        
        Args:
            method: Metode pooling ('tfidf', 'frequency', 'position', 'hybrid')
        """
        self.method = method
        self.tfidf_vectorizer = None
        self.word_weights = {}
        self.corpus_stats = {}
        
    def fit(self, corpus: List[List[str]], verse_texts: List[str] = None):
        """
        Fit model berdasarkan korpus
        
        Args:
            corpus: List of tokenized sentences
            verse_texts: List of raw verse texts (untuk TF-IDF)
        """
        if self.method == 'tfidf':
            self._fit_tfidf(verse_texts)
        elif self.method == 'frequency':
            self._fit_frequency(corpus)
        elif self.method == 'position':
            # Position-based tidak memerlukan fitting
            pass
        elif self.method == 'hybrid':
            self._fit_hybrid(corpus, verse_texts)
        else:
            raise ValueError(f"Method {self.method} not supported")
    
    def _fit_tfidf(self, verse_texts: List[str]):
        """
        Fit TF-IDF vectorizer
        """
        if not verse_texts:
            raise ValueError("Verse texts required for TF-IDF method")
        
        # Gabungkan semua teks ayat
        combined_texts = [' '.join(text.split()) for text in verse_texts]
        
        # Fit TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            token_pattern=r'\b\w+\b',
            max_features=10000
        )
        self.tfidf_vectorizer.fit(combined_texts)
        
        # Simpan vocabulary untuk akses cepat
        self.vocabulary = self.tfidf_vectorizer.vocabulary_
        self.idf = self.tfidf_vectorizer.idf_
        
        print(f"TF-IDF fitted with {len(self.vocabulary)} unique words")
    
    def _fit_frequency(self, corpus: List[List[str]]):
        """
        Fit frequency-based weighting
        """
        # Hitung frekuensi kata dalam korpus
        word_counts = Counter()
        total_words = 0
        
        for sentence in corpus:
            for word in sentence:
                word_counts[word] += 1
                total_words += 1
        
        # Hitung inverse frequency weight
        for word, count in word_counts.items():
            # Inverse frequency: kata yang jarang mendapat bobot lebih tinggi
            self.word_weights[word] = np.log(total_words / count)
        
        print(f"Frequency weights computed for {len(self.word_weights)} words")
    
    def _fit_hybrid(self, corpus: List[List[str]], verse_texts: List[str]):
        """
        Fit hybrid method (TF-IDF + frequency)
        """
        # Fit TF-IDF
        self._fit_tfidf(verse_texts)
        
        # Fit frequency
        word_counts = Counter()
        total_words = 0
        
        for sentence in corpus:
            for word in sentence:
                word_counts[word] += 1
                total_words += 1
        
        # Kombinasikan weights
        for word in set(self.word_weights.keys()) | set(word_counts.keys()):
            tfidf_weight = self.word_weights.get(word, 0)
            freq_weight = np.log(total_words / word_counts.get(word, 1))
            
            # Rata-rata dari kedua weight
            self.word_weights[word] = (tfidf_weight + freq_weight) / 2
        
        print(f"Hybrid weights computed for {len(self.word_weights)} words")
    
    def get_word_weight(self, word: str, position: int = None) -> float:
        """
        Mendapatkan bobot untuk kata tertentu
        
        Args:
            word: Kata yang akan diberi bobot
            position: Posisi kata dalam ayat (untuk position-based)
            
        Returns:
            Bobot kata
        """
        if self.method == 'tfidf':
            return self._get_tfidf_weight(word)
        elif self.method == 'frequency':
            return self.word_weights.get(word, 1.0)
        elif self.method == 'position':
            return self._get_position_weight(word, position)
        elif self.method == 'hybrid':
            return self.word_weights.get(word, 1.0)
        else:
            return 1.0  # Default weight
    
    def _get_tfidf_weight(self, word: str) -> float:
        """
        Mendapatkan TF-IDF weight untuk kata
        """
        if not self.tfidf_vectorizer:
            return 1.0
        
        try:
            # Dapatkan IDF score
            if word in self.vocabulary:
                word_idx = self.vocabulary[word]
                return self.idf[word_idx]
            else:
                return 1.0  # Default untuk kata yang tidak ada dalam vocabulary
        except Exception:
            return 1.0
    
    def _get_position_weight(self, word: str, position: int) -> float:
        """
        Mendapatkan position-based weight
        Kata di awal dan akhir ayat mendapat bobot lebih tinggi
        """
        if position is None:
            return 1.0
        
        # Bobot berdasarkan posisi: awal dan akhir lebih penting
        if position == 0:  # Kata pertama
            return 1.5
        elif position == -1:  # Kata terakhir
            return 1.3
        else:
            # Bobot menurun dari tengah ke ujung
            return 1.0
    
    def aggregate_vectors(self, token_vectors: List[np.ndarray], 
                         tokens: List[str] = None) -> np.ndarray:
        """
        Agregasi vektor kata menjadi vektor ayat dengan weighted pooling
        
        Args:
            token_vectors: List vektor kata
            tokens: List token (untuk weighted pooling)
            
        Returns:
            Vektor ayat hasil agregasi
        """
        if not token_vectors:
            return None
        
        if self.method == 'mean':
            # Mean pooling (baseline)
            return np.mean(token_vectors, axis=0)
        
        elif self.method in ['tfidf', 'frequency', 'hybrid']:
            # Weighted pooling
            if not tokens or len(tokens) != len(token_vectors):
                # Fallback ke mean pooling jika tokens tidak tersedia
                return np.mean(token_vectors, axis=0)
            
            weights = []
            for i, token in enumerate(tokens):
                weight = self.get_word_weight(token, position=i)
                weights.append(weight)
            
            # Normalisasi weights
            weights = np.array(weights)
            weights = weights / np.sum(weights)
            
            # Weighted average
            weighted_vectors = [w * v for w, v in zip(weights, token_vectors)]
            return np.sum(weighted_vectors, axis=0)
        
        elif self.method == 'position':
            # Position-based weighted pooling
            weights = []
            for i in range(len(token_vectors)):
                weight = self._get_position_weight(None, i)
                weights.append(weight)
            
            # Normalisasi weights
            weights = np.array(weights)
            weights = weights / np.sum(weights)
            
            # Weighted average
            weighted_vectors = [w * v for w, v in zip(weights, token_vectors)]
            return np.sum(weighted_vectors, axis=0)
        
        else:
            # Default: mean pooling
            return np.mean(token_vectors, axis=0)
    
    def save_model(self, filepath: str):
        """
        Simpan model weighted pooling
        """
        model_data = {
            'method': self.method,
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'word_weights': self.word_weights,
            'vocabulary': getattr(self, 'vocabulary', {}),
            'idf': getattr(self, 'idf', None)
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Weighted pooling model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Muat model weighted pooling
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.method = model_data['method']
        self.tfidf_vectorizer = model_data['tfidf_vectorizer']
        self.word_weights = model_data['word_weights']
        self.vocabulary = model_data.get('vocabulary', {})
        self.idf = model_data.get('idf', None)
        
        print(f"Weighted pooling model loaded from {filepath}")


class FastTextWeightedPooling:
    """
    Wrapper untuk integrasi weighted pooling dengan FastText model
    """
    
    def __init__(self, fasttext_model, pooling_method: str = 'tfidf'):
        """
        Inisialisasi FastText dengan weighted pooling
        
        Args:
            fasttext_model: Instance FastTextModel
            pooling_method: Metode pooling ('mean', 'tfidf', 'frequency', 'position', 'hybrid')
        """
        self.fasttext_model = fasttext_model
        self.pooling_method = pooling_method
        self.weighted_pooling = WeightedPooling(method=pooling_method)
        
    def fit_pooling(self, preprocessed_verses: Dict[str, Dict[str, Any]]):
        """
        Fit weighted pooling berdasarkan data ayat
        
        Args:
            preprocessed_verses: Data ayat yang telah diproses
        """
        # Siapkan corpus untuk fitting
        corpus = []
        verse_texts = []
        
        for verse_id, verse_info in preprocessed_verses.items():
            tokens = verse_info['tokens']
            corpus.append(tokens)
            verse_texts.append(verse_info['translation'])
        
        # Fit weighted pooling
        self.weighted_pooling.fit(corpus, verse_texts)
        
        print(f"Weighted pooling fitted with method: {self.pooling_method}")
    
    def create_verse_vectors_weighted(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membuat vektor ayat dengan weighted pooling
        """
        if self.fasttext_model.model is None:
            raise ValueError("FastText model belum dimuat")
        
        print(f"Creating verse vectors with {self.pooling_method} pooling...")
        
        # Simpan data ayat
        self.fasttext_model.verse_data = preprocessed_verses
        
        # Buat vektor untuk setiap ayat
        for verse_id, verse_info in preprocessed_verses.items():
            tokens = verse_info['tokens']
            verse_vector = self._calculate_verse_vector_weighted(tokens)
            if verse_vector is not None:
                self.fasttext_model.verse_vectors[verse_id] = verse_vector
        
        print(f"Created weighted vectors for {len(self.fasttext_model.verse_vectors)} verses")
    
    def _calculate_verse_vector_weighted(self, tokens: List[str]) -> np.ndarray:
        """
        Menghitung vektor ayat dengan weighted pooling
        """
        if not tokens:
            return None
        
        # Kumpulkan vektor untuk setiap kata
        token_vectors = []
        valid_tokens = []
        
        for token in tokens:
            try:
                vector = self.fasttext_model.model.wv[token]
                token_vectors.append(vector)
                valid_tokens.append(token)
            except Exception as e:
                print(f"Error getting vector for token '{token}': {e}")
                continue
        
        if not token_vectors:
            return None
        
        # Gunakan weighted pooling untuk agregasi
        verse_vector = self.weighted_pooling.aggregate_vectors(token_vectors, valid_tokens)
        
        # Normalisasi L2
        norm = np.linalg.norm(verse_vector)
        if norm > 0:
            verse_vector = verse_vector / norm
        
        return verse_vector
    
    def save_pooling_model(self, filepath: str):
        """
        Simpan model weighted pooling
        """
        self.weighted_pooling.save_model(filepath)
    
    def load_pooling_model(self, filepath: str):
        """
        Muat model weighted pooling
        """
        self.weighted_pooling.load_model(filepath) 