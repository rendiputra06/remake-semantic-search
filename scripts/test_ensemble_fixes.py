#!/usr/bin/env python3
"""
Script untuk menguji perbaikan ensemble test
- Bug fix untuk limit tak terbatas
- Meta-ensemble auto-initialization
- UI improvements
"""

import sys
import os
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ensemble_api():
    """Test ensemble API dengan berbagai parameter"""
    
    base_url = "http://localhost:5000"
    
    # Test cases
    test_cases = [
        {
            "name": "Test dengan limit 10",
            "data": {
                "query": "ibadah",
                "method": "weighted",
                "threshold": 0.5,
                "limit": 10,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test dengan limit tak terbatas (0)",
            "data": {
                "query": "ibadah",
                "method": "weighted",
                "threshold": 0.5,
                "limit": 0,  # Tak terbatas
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test meta-ensemble",
            "data": {
                "query": "shalat",
                "method": "meta",
                "threshold": 0.5,
                "limit": 20,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test voting method",
            "data": {
                "query": "puasa",
                "method": "voting",
                "threshold": 0.5,
                "limit": 15,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        }
    ]
    
    print("🧪 Testing Ensemble API Fixes")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/models/ensemble/test",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    results = data.get('results', [])
                    print(f"✅ Success: {len(results)} results found")
                    
                    # Show first few results
                    for j, res in enumerate(results[:3]):
                        print(f"   {j+1}. {res.get('surah_name', 'N/A')} {res.get('ayat_number', 'N/A')} - Score: {res.get('similarity', 0):.3f}")
                    
                    if len(results) > 3:
                        print(f"   ... and {len(results) - 3} more results")
                        
                else:
                    print(f"❌ API Error: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

def test_meta_ensemble_initialization():
    """Test meta-ensemble auto-initialization"""
    
    print("\n🔧 Testing Meta-Ensemble Auto-Initialization")
    print("=" * 50)
    
    try:
        from backend.meta_ensemble import MetaEnsembleModel
        
        # Test meta-ensemble initialization
        meta_model = MetaEnsembleModel()
        
        # Test auto-initialization
        print("Testing auto-initialization...")
        initialized = meta_model.auto_initialize()
        
        if initialized:
            print("✅ Meta-ensemble auto-initialization successful")
        else:
            print("ℹ️ Meta-ensemble model already exists")
        
        # Test model validation
        print("Testing model validation...")
        is_valid, message = meta_model.validate_model()
        
        if is_valid:
            print("✅ Meta-ensemble model validation successful")
        else:
            print(f"❌ Meta-ensemble validation failed: {message}")
        
        # Test prediction
        print("Testing prediction...")
        prediction = meta_model.predict_relevance(0.7, 0.8, 0.6, 3, 12)
        print(f"✅ Prediction successful: {prediction}")
        
    except Exception as e:
        print(f"❌ Meta-ensemble test failed: {e}")

def test_ensemble_embedding_fix():
    """Test ensemble embedding limit fix"""
    
    print("\n🔧 Testing Ensemble Embedding Limit Fix")
    print("=" * 50)
    
    try:
        from backend.ensemble_embedding import EnsembleEmbeddingModel
        from backend.word2vec_model import Word2VecModel
        from backend.fasttext_model import FastTextModel
        from backend.glove_model import GloVeModel
        
        # Initialize models (this might take time)
        print("Initializing models...")
        w2v_model = Word2VecModel()
        ft_model = FastTextModel()
        glove_model = GloVeModel()
        
        # Create ensemble
        ensemble = EnsembleEmbeddingModel(
            w2v_model, ft_model, glove_model,
            use_meta_ensemble=True
        )
        
        # Load models
        ensemble.load_models()
        ensemble.load_verse_vectors()
        
        # Test with limited results
        print("Testing with limit=10...")
        results_limited = ensemble.search("ibadah", limit=10, threshold=0.5)
        print(f"✅ Limited results: {len(results_limited)} found")
        
        # Test with unlimited results
        print("Testing with limit=0 (unlimited)...")
        results_unlimited = ensemble.search("ibadah", limit=0, threshold=0.5)
        print(f"✅ Unlimited results: {len(results_unlimited)} found")
        
        # Verify unlimited returns more or equal results
        if len(results_unlimited) >= len(results_limited):
            print("✅ Unlimited limit fix working correctly")
        else:
            print("❌ Unlimited limit fix may have issues")
            
    except Exception as e:
        print(f"❌ Ensemble embedding test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Ensemble Test Suite")
    print("=" * 50)
    
    # Test API endpoints
    test_ensemble_api()
    
    # Test meta-ensemble initialization
    test_meta_ensemble_initialization()
    
    # Test ensemble embedding fix
    test_ensemble_embedding_fix()
    
    print("\n🎉 Test suite completed!")
    print("=" * 50) 