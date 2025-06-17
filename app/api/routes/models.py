"""
Model management related routes for the semantic search API.
"""
from flask import Blueprint, session
from backend.db import get_user_settings
from ..utils import create_response, error_response

models_bp = Blueprint('models', __name__)

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
        }
    ]
    
    return create_response(
        data=available_models,
        message='Daftar model berhasil diambil'
    )

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