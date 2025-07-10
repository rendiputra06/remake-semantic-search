"""
Modul untuk implementasi attention mechanism dalam embedding
Meningkatkan metode agregasi vektor kata dengan self-attention
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import pickle
import os

class SelfAttention:
    """
    Implementasi self-attention sederhana untuk pembobotan kata
    """
    
    def __init__(self, vector_dim: int = 200, attention_dim: int = 64):
        """
        Inisialisasi self-attention
        
        Args:
            vector_dim: Dimensi vektor input
            attention_dim: Dimensi attention layer
        """
        self.vector_dim = vector_dim
        self.attention_dim = attention_dim
        
        # Initialize attention weights
        self.W_q = np.random.randn(vector_dim, attention_dim) * 0.1
        self.W_k = np.random.randn(vector_dim, attention_dim) * 0.1
        self.W_v = np.random.randn(vector_dim, attention_dim) * 0.1
        
        # Normalize weights
        self.W_q = self.W_q / np.linalg.norm(self.W_q, axis=0)
        self.W_k = self.W_k / np.linalg.norm(self.W_k, axis=0)
        self.W_v = self.W_v / np.linalg.norm(self.W_v, axis=0)
    
    def compute_attention(self, vectors: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Menghitung attention weights dan weighted vectors
        
        Args:
            vectors: List vektor kata
            
        Returns:
            Tuple (attention_weights, weighted_vectors)
        """
        if not vectors:
            return None, None
        
        # Convert to numpy array
        vectors_array = np.array(vectors)  # Shape: (n_tokens, vector_dim)
        n_tokens = vectors_array.shape[0]
        
        # Compute Query, Key, Value matrices
        Q = vectors_array @ self.W_q  # Shape: (n_tokens, attention_dim)
        K = vectors_array @ self.W_k  # Shape: (n_tokens, attention_dim)
        V = vectors_array @ self.W_v  # Shape: (n_tokens, attention_dim)
        
        # Compute attention scores
        attention_scores = Q @ K.T  # Shape: (n_tokens, n_tokens)
        
        # Scale attention scores
        attention_scores = attention_scores / np.sqrt(self.attention_dim)
        
        # Apply softmax to get attention weights
        attention_weights = self._softmax(attention_scores, axis=1)
        
        # Compute weighted values
        weighted_values = attention_weights @ V  # Shape: (n_tokens, attention_dim)
        
        # Project back to original dimension
        weighted_vectors = weighted_values @ self.W_v.T  # Shape: (n_tokens, vector_dim)
        
        return attention_weights, weighted_vectors
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """
        Compute softmax function
        """
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def save_model(self, filepath: str):
        """
        Simpan model attention
        """
        model_data = {
            'vector_dim': self.vector_dim,
            'attention_dim': self.attention_dim,
            'W_q': self.W_q,
            'W_k': self.W_k,
            'W_v': self.W_v
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Attention model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Muat model attention
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vector_dim = model_data['vector_dim']
        self.attention_dim = model_data['attention_dim']
        self.W_q = model_data['W_q']
        self.W_k = model_data['W_k']
        self.W_v = model_data['W_v']
        
        print(f"Attention model loaded from {filepath}")


class AttentionEmbedding:
    """
    Implementasi attention-based embedding untuk FastText
    """
    
    def __init__(self, fasttext_model, attention_dim: int = 64):
        """
        Inisialisasi attention embedding
        
        Args:
            fasttext_model: Instance FastTextModel
            attention_dim: Dimensi attention layer
        """
        self.fasttext_model = fasttext_model
        self.attention_dim = attention_dim
        self.attention = None
        
        # Initialize attention jika model sudah dimuat
        if hasattr(fasttext_model, 'model') and fasttext_model.model is not None:
            vector_dim = fasttext_model.model.vector_size
            self.attention = SelfAttention(vector_dim, attention_dim)
    
    def initialize_attention(self):
        """
        Initialize attention mechanism
        """
        if self.fasttext_model.model is None:
            raise ValueError("FastText model belum dimuat")
        
        vector_dim = self.fasttext_model.model.vector_size
        self.attention = SelfAttention(vector_dim, self.attention_dim)
        print(f"Attention mechanism initialized with dim {vector_dim} -> {self.attention_dim}")
    
    def create_verse_vectors_attention(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membuat vektor ayat dengan attention mechanism
        """
        if self.fasttext_model.model is None:
            raise ValueError("FastText model belum dimuat")
        
        if self.attention is None:
            self.initialize_attention()
        
        print("Creating verse vectors with attention mechanism...")
        
        # Simpan data ayat
        self.fasttext_model.verse_data = preprocessed_verses
        
        # Buat vektor untuk setiap ayat
        for verse_id, verse_info in preprocessed_verses.items():
            tokens = verse_info['tokens']
            verse_vector = self._calculate_verse_vector_attention(tokens)
            if verse_vector is not None:
                self.fasttext_model.verse_vectors[verse_id] = verse_vector
        
        print(f"Created attention-based vectors for {len(self.fasttext_model.verse_vectors)} verses")
    
    def _calculate_verse_vector_attention(self, tokens: List[str]) -> np.ndarray:
        """
        Menghitung vektor ayat dengan attention mechanism
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
        
        # Apply attention mechanism
        attention_weights, weighted_vectors = self.attention.compute_attention(token_vectors)
        
        if attention_weights is None:
            return None
        
        # Aggregate weighted vectors (mean pooling)
        verse_vector = np.mean(weighted_vectors, axis=0)
        
        # Normalisasi L2
        norm = np.linalg.norm(verse_vector)
        if norm > 0:
            verse_vector = verse_vector / norm
        
        return verse_vector
    
    def get_attention_weights(self, tokens: List[str]) -> Optional[np.ndarray]:
        """
        Mendapatkan attention weights untuk debugging
        """
        if not tokens:
            return None
        
        # Kumpulkan vektor untuk setiap kata
        token_vectors = []
        for token in tokens:
            try:
                vector = self.fasttext_model.model.wv[token]
                token_vectors.append(vector)
            except Exception:
                continue
        
        if not token_vectors:
            return None
        
        # Compute attention weights
        attention_weights, _ = self.attention.compute_attention(token_vectors)
        return attention_weights
    
    def save_attention_model(self, filepath: str):
        """
        Simpan model attention
        """
        if self.attention:
            self.attention.save_model(filepath)
    
    def load_attention_model(self, filepath: str):
        """
        Muat model attention
        """
        if self.attention is None:
            self.initialize_attention()
        
        self.attention.load_model(filepath)


class MultiHeadAttention:
    """
    Implementasi multi-head attention untuk embedding yang lebih kompleks
    """
    
    def __init__(self, vector_dim: int = 200, num_heads: int = 4, attention_dim: int = 64):
        """
        Inisialisasi multi-head attention
        
        Args:
            vector_dim: Dimensi vektor input
            num_heads: Jumlah attention heads
            attention_dim: Dimensi per attention head
        """
        self.vector_dim = vector_dim
        self.num_heads = num_heads
        self.attention_dim = attention_dim
        self.head_dim = attention_dim // num_heads
        
        # Initialize attention heads
        self.attention_heads = []
        for _ in range(num_heads):
            head = SelfAttention(vector_dim, self.head_dim)
            self.attention_heads.append(head)
    
    def compute_multi_head_attention(self, vectors: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Menghitung multi-head attention
        
        Args:
            vectors: List vektor kata
            
        Returns:
            Tuple (attention_weights, weighted_vectors)
        """
        if not vectors:
            return None, None
        
        # Compute attention for each head
        head_outputs = []
        head_weights = []
        
        for head in self.attention_heads:
            weights, output = head.compute_attention(vectors)
            if weights is not None and output is not None:
                head_outputs.append(output)
                head_weights.append(weights)
        
        if not head_outputs:
            return None, None
        
        # Concatenate head outputs
        concatenated_output = np.concatenate(head_outputs, axis=1)
        
        # Average attention weights across heads
        avg_attention_weights = np.mean(head_weights, axis=0)
        
        return avg_attention_weights, concatenated_output
    
    def save_model(self, filepath: str):
        """
        Simpan model multi-head attention
        """
        model_data = {
            'vector_dim': self.vector_dim,
            'num_heads': self.num_heads,
            'attention_dim': self.attention_dim,
            'head_dim': self.head_dim,
            'attention_heads': self.attention_heads
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Multi-head attention model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        Muat model multi-head attention
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.vector_dim = model_data['vector_dim']
        self.num_heads = model_data['num_heads']
        self.attention_dim = model_data['attention_dim']
        self.head_dim = model_data['head_dim']
        self.attention_heads = model_data['attention_heads']
        
        print(f"Multi-head attention model loaded from {filepath}")


class FastTextAttentionEmbedding:
    """
    Wrapper untuk integrasi attention embedding dengan FastText model
    """
    
    def __init__(self, fasttext_model, attention_type: str = 'single', num_heads: int = 4):
        """
        Inisialisasi FastText dengan attention embedding
        
        Args:
            fasttext_model: Instance FastTextModel
            attention_type: Tipe attention ('single', 'multi')
            num_heads: Jumlah heads untuk multi-head attention
        """
        self.fasttext_model = fasttext_model
        self.attention_type = attention_type
        self.num_heads = num_heads
        self.attention_embedding = None
        
    def initialize_attention(self):
        """
        Initialize attention mechanism
        """
        if self.fasttext_model.model is None:
            raise ValueError("FastText model belum dimuat")
        
        vector_dim = self.fasttext_model.model.vector_size
        
        if self.attention_type == 'single':
            self.attention_embedding = AttentionEmbedding(self.fasttext_model)
        elif self.attention_type == 'multi':
            # Multi-head attention akan diimplementasikan nanti
            self.attention_embedding = AttentionEmbedding(self.fasttext_model)
        else:
            raise ValueError(f"Attention type {self.attention_type} not supported")
        
        print(f"Attention embedding initialized with type: {self.attention_type}")
    
    def create_verse_vectors_attention(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membuat vektor ayat dengan attention mechanism
        """
        if self.attention_embedding is None:
            self.initialize_attention()
        
        self.attention_embedding.create_verse_vectors_attention(preprocessed_verses)
    
    def save_attention_model(self, filepath: str):
        """
        Simpan model attention
        """
        if self.attention_embedding:
            self.attention_embedding.save_attention_model(filepath)
    
    def load_attention_model(self, filepath: str):
        """
        Muat model attention
        """
        if self.attention_embedding is None:
            self.initialize_attention()
        
        self.attention_embedding.load_attention_model(filepath) 