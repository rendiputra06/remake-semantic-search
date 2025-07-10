"""
Model management related routes for the semantic search API.
"""
from flask import Blueprint, session, request
from backend.db import get_user_settings
from ..utils import create_response, error_response
from backend.ensemble_embedding import EnsembleEmbeddingModel
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
from backend.ensemble_embedding import EnsembleEmbeddingModel
from backend.meta_ensemble import MetaEnsembleModel, create_training_data_from_evaluation_results
import numpy as np
from backend.db import get_global_thresholds

models_bp = Blueprint('models', __name__)

# Global model instances
word2vec_model = None
fasttext_model = None
glove_model = None
ensemble_model = None

def init_models():
    """
    Initialize all models if not already initialized
    """
    global word2vec_model, fasttext_model, glove_model, ensemble_model
    
    if word2vec_model is None:
        word2vec_model = Word2VecModel()
        word2vec_model.load_model()
        word2vec_model.load_verse_vectors()
        
    if fasttext_model is None:
        fasttext_model = FastTextModel()
        fasttext_model.load_model()
        fasttext_model.load_verse_vectors()
        
    if glove_model is None:
        glove_model = GloVeModel()
        glove_model.load_model()
        glove_model.load_verse_vectors()
        
    if ensemble_model is None:
        ensemble_model = EnsembleEmbeddingModel(word2vec_model, fasttext_model, glove_model)
        ensemble_model.load_models()
        ensemble_model.load_verse_vectors()

def get_word_inspection_data(word: str, model_type: str) -> dict:
    """
    Helper function to get inspection data for a single word and model.
    """
    if not word:
        raise ValueError("Kata tidak boleh kosong")

    # This function assumes models are initialized. A global init call might be needed.
    # init_models() # Uncomment if you want to ensure models are loaded on every call

    # Determine which model to use
    model_map = {
        'word2vec': word2vec_model,
        'fasttext': fasttext_model,
        'glove': glove_model,
        'ensemble': ensemble_model
    }
    model = model_map.get(model_type)
    if not model:
        raise ValueError(f"Model type '{model_type}' tidak valid.")

    # Calculate vector
    if model_type == 'ensemble':
        vector = model._calculate_query_vector([word])
    else:
        # Check if word is in vocabulary
        if word not in model.model.wv:
            raise ValueError(f"Kata '{word}' tidak ditemukan dalam vocabulary model {model_type}")
        vector = model.model.wv[word]
        
    if vector is None:
        raise ValueError(f"Kata '{word}' tidak ditemukan dalam model {model_type}")

    vector_list = vector.tolist()
    result = {
        'model_type': model_type,
        'vector': vector_list,
        'vector_dimension': len(vector_list),
        'vector_norm': float(np.linalg.norm(vector))
    }

    # Get similar words
    try:
        if model_type == 'ensemble':
            # For ensemble, find most similar from the pre-calculated verse vectors
            similar_verses = model.search(word, limit=10, threshold=0.1) # Use search as a proxy
            # This is an approximation; a true 'similar word' isn't directly available.
            # We can extract keywords from the top verses as a substitute.
            # For now, we'll return an empty list as a placeholder.
            result['similar_words'] = [] # Placeholder
        else:
            similar_items = model.model.wv.most_similar(word, topn=10)
            result['similar_words'] = [
                {'word': w, 'similarity': float(s)} 
                for w, s in similar_items
            ]
    except Exception:
        result['similar_words'] = [] # If a word has no similar words

    return result

@models_bp.route('/models', methods=['GET'])
def get_models():
    """
    Endpoint untuk mendapatkan model yang tersedia
    """
    available_models = [
        {
            'id': 'word2vec',
            'name': 'Word2Vec',
            'description': 'Model yang mengubah kata menjadi vektor berdasarkan konteks dan mengidentifikasi hubungan semantik antar kata.'
        },
        {
            'id': 'fasttext',
            'name': 'FastText',
            'description': 'Model yang memperluas Word2Vec dengan menambahkan representasi sub-kata, sehingga dapat menangani kata yang tidak ada dalam kosakata (out-of-vocabulary words).'
        },
        {
            'id': 'glove',
            'name': 'GloVe',
            'description': 'Global Vectors for Word Representation. Model yang fokus pada statistik co-occurrence global, menangkap makna semantik dan sintaksis kata.'
        },
        {
            'id': 'ensemble',
            'name': 'Ensemble',
            'description': 'Gabungan Word2Vec, FastText, dan GloVe untuk hasil yang lebih akurat dan stabil.'
        }
    ]
    
    return create_response(
        data=available_models,
        message='Daftar model berhasil diambil'
    )

@models_bp.route('/inspect', methods=['POST'])
def inspect_model_comparison():
    """
    Endpoint untuk menginspeksi dan membandingkan sebuah kata pada dua model.
    """
    data = request.get_json()
    word = data.get('word')
    model_left = data.get('model_left')
    model_right = data.get('model_right')

    if not all([word, model_left, model_right]):
        return error_response('Parameter "word", "model_left", dan "model_right" dibutuhkan', 400)
    
    try:
        # Ensure all models are loaded before inspection
        init_models()
        
        data_left = get_word_inspection_data(word, model_left)
        data_right = get_word_inspection_data(word, model_right)
        
        response_data = {
            'word': word,
            'left': data_left,
            'right': data_right
        }
        
        return create_response(data=response_data, message='Inspeksi perbandingan model berhasil')

    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f'Error internal: {str(e)}', 500)

@models_bp.route('/user_settings', methods=['GET'])
def user_settings():
    """
    Endpoint untuk mendapatkan pengaturan pengguna
    """
    if 'user_id' not in session:
        return error_response(401, 'Anda harus login untuk mengakses pengaturan')
    
    settings = get_user_settings(session['user_id'])
    
    # Handle result_limit 0 sebagai tak terbatas
    result_limit = settings.get('result_limit', 10)
    if result_limit == 0:
        result_limit = 1000  # Gunakan 1000 sebagai limit maksimal untuk tak terbatas
    
    return create_response(
        data={
            'default_model': settings.get('default_model', 'word2vec'),
            'result_limit': result_limit,
            'threshold': settings.get('threshold', 0.5)
        },
        message='Pengaturan pengguna berhasil diambil'
    )

@models_bp.route('/default_settings', methods=['GET'])
def default_settings():
    """
    Endpoint untuk mendapatkan pengaturan default (public, tidak memerlukan login)
    """
    thresholds = get_global_thresholds()
    return create_response(
        data={
            'default_model': 'word2vec',
            'result_limit': 10,
            'thresholds': thresholds
        },
        message='Pengaturan default berhasil diambil'
    )

@models_bp.route('/search/ensemble', methods=['POST'])
def ensemble_search():
    """
    Endpoint untuk pencarian menggunakan ensemble model
    """
    data = request.get_json()
    query = data.get('query')
    limit = data.get('limit', 10)
    threshold = data.get('threshold', 0.5)
    use_meta_ensemble = data.get('use_meta_ensemble', False)
    
    if not query:
        return error_response('Query tidak boleh kosong', 400)
        
    try:
        # Inisialisasi model jika belum
        init_models()
        
        # Buat ensemble model dengan opsi meta-ensemble
        ensemble = EnsembleEmbeddingModel(
            word2vec_model, fasttext_model, glove_model,
            use_meta_ensemble=use_meta_ensemble
        )
        ensemble.load_models()
        
        # Lakukan pencarian
        results = ensemble.search(query, limit=limit, threshold=threshold)
        
        return create_response(
            data=results,
            message='Pencarian berhasil'
        )
        
    except Exception as e:
        return error_response(f'Error saat melakukan pencarian: {str(e)}', 500)

@models_bp.route('/meta_ensemble/train', methods=['POST'])
def train_meta_ensemble():
    """
    Endpoint untuk melatih meta-ensemble model
    """
    data = request.get_json()
    training_data = data.get('training_data', [])
    
    if not training_data:
        return error_response('Training data tidak boleh kosong', 400)
    
    try:
        meta_ensemble = MetaEnsembleModel()
        result = meta_ensemble.train(training_data)
        meta_ensemble.save_model()
        
        return create_response(
            data=result,
            message='Meta-ensemble model berhasil dilatih'
        )
        
    except Exception as e:
        return error_response(f'Error saat melatih meta-ensemble: {str(e)}', 500)

@models_bp.route('/meta_ensemble/predict', methods=['POST'])
def predict_meta_ensemble():
    """
    Endpoint untuk prediksi menggunakan meta-ensemble model
    """
    data = request.get_json()
    word2vec_score = data.get('word2vec_score', 0.0)
    fasttext_score = data.get('fasttext_score', 0.0)
    glove_score = data.get('glove_score', 0.0)
    query_length = data.get('query_length', 0)
    verse_length = data.get('verse_length', 0)
    
    try:
        meta_ensemble = MetaEnsembleModel()
        meta_ensemble.load_model()
        
        result = meta_ensemble.predict_relevance(
            word2vec_score, fasttext_score, glove_score,
            query_length, verse_length
        )
        
        return create_response(
            data=result,
            message='Prediksi meta-ensemble berhasil'
        )
        
    except Exception as e:
        return error_response(f'Error saat prediksi meta-ensemble: {str(e)}', 500)

@models_bp.route('/meta_ensemble/feature_importance', methods=['GET'])
def get_meta_ensemble_feature_importance():
    """
    Endpoint untuk mendapatkan feature importance dari meta-ensemble model
    """
    try:
        meta_ensemble = MetaEnsembleModel()
        meta_ensemble.load_model()
        
        importance = meta_ensemble.get_feature_importance()
        
        return create_response(
            data=importance,
            message='Feature importance berhasil diambil'
        )
        
    except Exception as e:
        return error_response(f'Error saat mengambil feature importance: {str(e)}', 500)

@models_bp.route('/meta_ensemble/status', methods=['GET'])
def get_meta_ensemble_status():
    """
    Endpoint untuk mengecek status meta-ensemble model
    """
    try:
        meta_ensemble = MetaEnsembleModel()
        meta_ensemble.load_model()
        
        return create_response(
            data={
                'is_trained': meta_ensemble.is_trained,
                'model_path': meta_ensemble.model_path
            },
            message='Status meta-ensemble berhasil diambil'
        )
        
    except Exception as e:
        return create_response(
            data={
                'is_trained': False,
                'error': str(e)
            },
            message='Meta-ensemble model tidak tersedia'
        )