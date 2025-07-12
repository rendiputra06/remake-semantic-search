"""
Modul untuk Meta-Ensemble dengan Machine Learning
Menggunakan Logistic Regression untuk menggabungkan skor dari model individual
"""
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class MetaEnsembleModel:
    """
    Meta-ensemble model menggunakan Logistic Regression untuk menggabungkan skor model individual
    """
    def __init__(self, model_path: str = None):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        if model_path is None:
            model_path = os.path.join(base_dir, '../models/meta_ensemble_model.pkl')
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, 
                        word2vec_score: float, 
                        fasttext_score: float, 
                        glove_score: float,
                        query_length: int = 0,
                        verse_length: int = 0) -> np.ndarray:
        """
        Menyiapkan feature vector untuk meta-ensemble
        """
        features = [
            word2vec_score,
            fasttext_score, 
            glove_score,
            query_length,
            verse_length,
            # Feature tambahan
            word2vec_score * fasttext_score,  # Interaction term
            word2vec_score * glove_score,
            fasttext_score * glove_score,
            np.mean([word2vec_score, fasttext_score, glove_score]),  # Average score
            np.std([word2vec_score, fasttext_score, glove_score]),   # Score variance
            max(word2vec_score, fasttext_score, glove_score),        # Max score
            min(word2vec_score, fasttext_score, glove_score)         # Min score
        ]
        return np.array(features).reshape(1, -1)
    
    def generate_synthetic_training_data(self) -> List[Dict[str, Any]]:
        """
        Generate synthetic training data menggunakan heuristik sederhana
        """
        training_data = []
        
        # Generate berbagai kombinasi skor
        score_combinations = [
            # High relevance cases
            (0.8, 0.7, 0.9, 3, 15, True),
            (0.9, 0.8, 0.7, 2, 12, True),
            (0.7, 0.9, 0.8, 4, 18, True),
            (0.8, 0.8, 0.8, 3, 10, True),
            
            # Medium relevance cases
            (0.6, 0.5, 0.7, 2, 8, True),
            (0.5, 0.6, 0.5, 3, 12, True),
            (0.7, 0.4, 0.6, 1, 6, True),
            
            # Low relevance cases
            (0.3, 0.2, 0.4, 1, 5, False),
            (0.2, 0.3, 0.1, 2, 8, False),
            (0.1, 0.1, 0.2, 1, 3, False),
            (0.0, 0.0, 0.0, 1, 4, False),
            
            # Mixed cases
            (0.8, 0.2, 0.6, 3, 10, True),
            (0.2, 0.8, 0.3, 2, 7, True),
            (0.6, 0.3, 0.8, 1, 9, True),
        ]
        
        for w2v, ft, glove, q_len, v_len, is_relevant in score_combinations:
            training_item = {
                'word2vec_score': w2v,
                'fasttext_score': ft,
                'glove_score': glove,
                'query_length': q_len,
                'verse_length': v_len,
                'is_relevant': is_relevant
            }
            training_data.append(training_item)
        
        return training_data
    
    def auto_initialize(self):
        """
        Auto-initialize meta-ensemble jika belum ada
        """
        if not os.path.exists(self.model_path):
            print("Meta-ensemble model not found. Initializing...")
            
            # Buat direktori jika belum ada
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Generate synthetic training data
            synthetic_data = self.generate_synthetic_training_data()
            
            # Train model
            self.train(synthetic_data)
            self.save_model()
            
            print("Meta-ensemble model initialized successfully!")
            return True
        return False
    
    def validate_model(self):
        """
        Validasi model sebelum digunakan
        """
        if not self.is_trained:
            return False, "Model belum dilatih"
        
        if self.model is None:
            return False, "Model tidak tersedia"
        
        if self.scaler is None:
            return False, "Scaler tidak tersedia"
        
        # Test prediction dengan data dummy
        try:
            test_result = self.predict_relevance(0.5, 0.5, 0.5, 3, 10)
            if not isinstance(test_result, dict):
                return False, "Prediction format tidak valid"
            return True, "Model valid"
        except Exception as e:
            return False, f"Model validation failed: {e}"
    
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Melatih meta-ensemble model dengan data training
        
        training_data format:
        [
            {
                'word2vec_score': float,
                'fasttext_score': float, 
                'glove_score': float,
                'query_length': int,
                'verse_length': int,
                'is_relevant': bool  # Ground truth
            },
            ...
        ]
        """
        if not training_data:
            raise ValueError("Training data tidak boleh kosong")
            
        # Prepare features dan labels
        X = []
        y = []
        
        for item in training_data:
            features = self.prepare_features(
                item['word2vec_score'],
                item['fasttext_score'], 
                item['glove_score'],
                item.get('query_length', 0),
                item.get('verse_length', 0)
            )
            X.append(features.flatten())
            y.append(1 if item['is_relevant'] else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Meta-ensemble model trained successfully!")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Training samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        
        self.is_trained = True
        
        return {
            'accuracy': accuracy,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict_relevance(self, 
                         word2vec_score: float, 
                         fasttext_score: float, 
                         glove_score: float,
                         query_length: int = 0,
                         verse_length: int = 0) -> Dict[str, Any]:
        """
        Memprediksi relevansi ayat menggunakan meta-ensemble model
        """
        if not self.is_trained:
            raise ValueError("Model belum dilatih. Jalankan train() terlebih dahulu.")
            
        features = self.prepare_features(
            word2vec_score, fasttext_score, glove_score, 
            query_length, verse_length
        )
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        relevance_prob = self.model.predict_proba(features_scaled)[0][1]  # Probability of relevant class
        relevance_score = float(relevance_prob)
        
        return {
            'relevance_score': relevance_score,
            'relevance_probability': relevance_prob,
            'is_relevant': relevance_prob > 0.5,
            'features': features.flatten().tolist()
        }
    
    def save_model(self, output_path: str = None):
        """
        Menyimpan model dan scaler
        """
        if not self.is_trained:
            raise ValueError("Model belum dilatih")
            
        if output_path is None:
            output_path = self.model_path
            
        # Pastikan direktori ada
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Simpan model dan scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(model_data, f)
            
        print(f"Meta-ensemble model saved to {output_path}")
    
    def load_model(self, input_path: str = None):
        """
        Enhanced model loading dengan fallback
        """
        if input_path is None:
            input_path = self.model_path
            
        try:
            with open(input_path, 'rb') as f:
                model_data = pickle.load(f)
                
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            
            print(f"Meta-ensemble model loaded from {input_path}")
            return True
            
        except FileNotFoundError:
            print(f"Meta-ensemble model not found at {input_path}")
            return False
        except Exception as e:
            print(f"Error loading meta-ensemble model: {e}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Mendapatkan importance dari setiap feature
        """
        if not self.is_trained:
            raise ValueError("Model belum dilatih")
            
        feature_names = [
            'word2vec_score', 'fasttext_score', 'glove_score',
            'query_length', 'verse_length',
            'w2v_ft_interaction', 'w2v_glove_interaction', 'ft_glove_interaction',
            'avg_score', 'score_variance', 'max_score', 'min_score'
        ]
        
        importance = dict(zip(feature_names, np.abs(self.model.coef_[0])))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

def create_training_data_from_evaluation_results(evaluation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Helper function untuk membuat training data dari hasil evaluasi
    """
    training_data = []
    
    for result in evaluation_results:
        # Ambil skor individual dari setiap model
        individual_scores = result.get('individual_scores', {})
        
        # Ground truth: apakah ayat ini relevan (TP)
        is_relevant = result.get('is_relevant', False)  # Harus diset berdasarkan ground truth
        
        training_item = {
            'word2vec_score': individual_scores.get('word2vec', 0.0),
            'fasttext_score': individual_scores.get('fasttext', 0.0),
            'glove_score': individual_scores.get('glove', 0.0),
            'query_length': result.get('query_length', 0),
            'verse_length': result.get('verse_length', 0),
            'is_relevant': is_relevant
        }
        
        training_data.append(training_item)
    
    return training_data 