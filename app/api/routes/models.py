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
import numpy as np

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
            'name': 'Ensemble (Voting)',
            'description': 'Gabungan Word2Vec, FastText, dan GloVe untuk hasil yang lebih akurat dan stabil.'
        }
    ]
    
    return create_response(
        data=available_models,
        message='Daftar model berhasil diambil'
    )

@models_bp.route('/models/inspect', methods=['POST'])
def inspect_model():
    """
    Endpoint untuk menginspeksi model dan vektor
    """
    data = request.get_json()
    word = data.get('word')
    model_type = data.get('model_type', 'word2vec')
    
    if not word:
        return error_response('Kata tidak boleh kosong', 400)
        
    try:
        # Inisialisasi model yang dipilih
        if model_type == 'ensemble':
            word2vec = init_model('word2vec')
            fasttext = init_model('fasttext')
            glove = init_model('glove')
            model = EnsembleEmbeddingModel(word2vec, fasttext, glove)
            model.load_models()
            vector = model._calculate_query_vector([word])
        else:
            model = init_model(model_type)
            vector = model._calculate_verse_vector([word])
            
        if vector is None:
            return error_response('Kata tidak ditemukan dalam model', 404)
            
        # Konversi vektor numpy ke list untuk JSON serialization
        vector = vector.tolist()
        
        # Tambahkan informasi tambahan
        result = {
            'word': word,
            'model_type': model_type,
            'vector': vector,
            'vector_dimension': len(vector),
            'vector_norm': float(np.linalg.norm(vector))
        }
        
        # Jika bukan ensemble, tambahkan similar words
        if model_type != 'ensemble':
            similar_words = model.model.wv.most_similar(word, topn=10)
            result['similar_words'] = [
                {'word': w, 'similarity': float(s)} 
                for w, s in similar_words
            ]
            
        return create_response(
            data=result,
            message='Inspeksi model berhasil'
        )
        
    except Exception as e:
        return error_response(f'Error saat menginspeksi model: {str(e)}', 500)

@models_bp.route('/user_settings', methods=['GET'])
def user_settings():
    """
    Endpoint untuk mendapatkan pengaturan pengguna
    """
    if 'user_id' not in session:
        return error_response(401, 'Anda harus login untuk mengakses pengaturan')
    
    settings = get_user_settings(session['user_id'])
    
    return create_response(
        data={
            'default_model': settings.get('default_model', 'word2vec'),
            'result_limit': settings.get('result_limit', 10),
            'threshold': settings.get('threshold', 0.5)
        },
        message='Pengaturan pengguna berhasil diambil'
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
    
    if not query:
        return error_response('Query tidak boleh kosong', 400)
        
    try:
        # Inisialisasi model jika belum
        init_models()
        
        # Lakukan pencarian
        results = ensemble_model.search(query, limit=limit, threshold=threshold)
        
        return create_response(
            data=results,
            message='Pencarian berhasil'
        )
        
    except Exception as e:
        return error_response(f'Error saat melakukan pencarian: {str(e)}', 500)