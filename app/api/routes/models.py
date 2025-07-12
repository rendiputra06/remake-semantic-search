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

# Global variables untuk caching model
_models_initialized = False
_cached_ensemble = None

def init_models():
    """
    Inisialisasi model dengan caching untuk menghindari reload berulang
    """
    global word2vec_model, fasttext_model, glove_model, _models_initialized
    
    if _models_initialized:
        return  # Skip jika sudah diinisialisasi
    
    print("Initializing models (first time)...")
    word2vec_model = Word2VecModel()
    fasttext_model = FastTextModel()
    glove_model = GloVeModel()
    
    # Load models
    word2vec_model.load_model()
    fasttext_model.load_model()
    glove_model.load_model()
    
    # Load verse vectors
    word2vec_model.load_verse_vectors()
    fasttext_model.load_verse_vectors()
    glove_model.load_verse_vectors()
    
    _models_initialized = True
    print("Models initialized and cached successfully!")

def get_or_create_ensemble(w2v_weight=1.0, ft_weight=1.0, glove_weight=1.0, use_meta_ensemble=False):
    """
    Get cached ensemble atau buat baru dengan parameter yang diberikan
    """
    # Buat ensemble baru dengan parameter yang diberikan
    ensemble = EnsembleEmbeddingModel(
        word2vec_model, fasttext_model, glove_model,
        word2vec_weight=w2v_weight,
        fasttext_weight=ft_weight,
        glove_weight=glove_weight,
        use_meta_ensemble=use_meta_ensemble
    )
    
    # Load models dan verse vectors (models sudah cached)
    ensemble.load_models()
    ensemble.load_verse_vectors()
    
    return ensemble

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

@models_bp.route('/ensemble/test', methods=['POST'])
def ensemble_test():
    """
    Endpoint untuk menguji dan memvisualisasikan hasil ensemble dengan parameter custom.
    """
    data = request.get_json()
    query = data.get('query')
    method = data.get('method', 'weighted')
    threshold = float(data.get('threshold', 0.5))
    limit = int(data.get('limit', 10))
    w2v_weight = float(data.get('w2v_weight', 1.0))
    ft_weight = float(data.get('ft_weight', 1.0))
    glove_weight = float(data.get('glove_weight', 1.0))
    use_meta_ensemble = (method == 'meta')

    if not query:
        return error_response('Query tidak boleh kosong', 400)

    try:
        # Initialize models sekali saja dengan caching
        init_models()
        
        # Buat instance ensemble dengan bobot custom dan opsi meta
        ensemble = get_or_create_ensemble(
            w2v_weight=w2v_weight,
            ft_weight=ft_weight,
            glove_weight=glove_weight,
            use_meta_ensemble=use_meta_ensemble
        )
        
        # Lakukan pencarian
        results = ensemble.search(query, limit=limit, threshold=threshold)
        total_count = len(results)
        # Jika limit=0, hanya kirim 100 hasil pertama ke frontend
        if limit == 0 and total_count > 100:
            results_to_send = results[:100]
        else:
            results_to_send = results
        
        # Siapkan data untuk visualisasi (skor individual, voting, meta)
        visual_data = []
        for r in results_to_send:
            visual_data.append({
                'verse_id': r.get('verse_id'),
                'surah_number': r.get('surah_number'),
                'ayat_number': r.get('ayat_number'),
                'similarity': r.get('similarity'),
                'word2vec': r.get('individual_scores', {}).get('word2vec'),
                'fasttext': r.get('individual_scores', {}).get('fasttext'),
                'glove': r.get('individual_scores', {}).get('glove'),
                'voting': r.get('model_count', None),
                'meta_ensemble_score': r.get('meta_ensemble_score', None),
                'meta_ensemble_probability': r.get('meta_ensemble_probability', None)
            })
        
        return create_response(
            data={
                'results': results_to_send,
                'visual_data': visual_data,
                'total_count': total_count
            },
            message='Uji ensemble berhasil'
        )
    except Exception as e:
        return error_response(f'Error saat uji ensemble: {str(e)}', 500)