"""
Script untuk melatih meta-ensemble model
"""
import sys
import os
import json
import numpy as np
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.meta_ensemble import MetaEnsembleModel

def create_synthetic_training_data(num_samples: int = 1000) -> List[Dict[str, Any]]:
    """
    Membuat data training sintetis untuk meta-ensemble
    """
    training_data = []
    
    for i in range(num_samples):
        # Generate random scores
        w2v_score = np.random.uniform(0, 1)
        ft_score = np.random.uniform(0, 1)
        glove_score = np.random.uniform(0, 1)
        
        # Generate random lengths
        query_length = np.random.randint(1, 10)
        verse_length = np.random.randint(10, 50)
        
        # Simple rule for relevance: if average score > 0.6 or max score > 0.8
        avg_score = (w2v_score + ft_score + glove_score) / 3
        max_score = max(w2v_score, ft_score, glove_score)
        is_relevant = avg_score > 0.6 or max_score > 0.8
        
        # Add some noise
        if np.random.random() < 0.1:  # 10% noise
            is_relevant = not is_relevant
        
        training_item = {
            'word2vec_score': float(w2v_score),
            'fasttext_score': float(ft_score),
            'glove_score': float(glove_score),
            'query_length': int(query_length),
            'verse_length': int(verse_length),
            'is_relevant': bool(is_relevant)
        }
        
        training_data.append(training_item)
    
    return training_data

def create_training_data_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Membuat data training dari file JSON yang berisi hasil evaluasi
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        training_data = []
        
        for item in data:
            # Extract individual scores
            individual_scores = item.get('individual_scores', {})
            
            # Ground truth: TP = relevant, FP = not relevant
            is_relevant = item.get('result_type') == 'TP'
            
            training_item = {
                'word2vec_score': individual_scores.get('word2vec', 0.0),
                'fasttext_score': individual_scores.get('fasttext', 0.0),
                'glove_score': individual_scores.get('glove', 0.0),
                'query_length': item.get('query_length', 0),
                'verse_length': item.get('verse_length', 0),
                'is_relevant': is_relevant
            }
            
            training_data.append(training_item)
        
        return training_data
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def main():
    """
    Main function untuk melatih meta-ensemble model
    """
    print("=== Meta-Ensemble Model Training ===")
    
    # Check if training data file exists
    training_file = "results/evaluation_results.json"
    
    if os.path.exists(training_file):
        print(f"Loading training data from {training_file}")
        training_data = create_training_data_from_file(training_file)
        if training_data:
            print(f"Loaded {len(training_data)} samples from file")
        else:
            print("Failed to load data from file, using synthetic data")
            training_data = create_synthetic_training_data(1000)
    else:
        print("Training data file not found, using synthetic data")
        training_data = create_synthetic_training_data(1000)
    
    # Create and train meta-ensemble model
    meta_ensemble = MetaEnsembleModel()
    
    print(f"Training meta-ensemble model with {len(training_data)} samples...")
    result = meta_ensemble.train(training_data)
    
    print(f"Training completed!")
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"Training samples: {result['training_samples']}")
    print(f"Test samples: {result['test_samples']}")
    
    # Save model
    meta_ensemble.save_model()
    
    # Show feature importance
    importance = meta_ensemble.get_feature_importance()
    print("\nFeature Importance:")
    for feature, score in list(importance.items())[:5]:  # Top 5
        print(f"  {feature}: {score:.4f}")
    
    print("\nMeta-ensemble model training completed successfully!")

if __name__ == "__main__":
    main() 