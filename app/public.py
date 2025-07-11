"""
Public routes for the application.
"""
from flask import Blueprint, render_template, request, session
from backend.db import get_db_connection, get_user_by_id

# Create blueprint
public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """
    Halaman utama aplikasi
    """
    return render_template('index.html')

@public_bp.route('/about')
def about():
    """
    Halaman tentang aplikasi
    """
    return render_template('about.html')

@public_bp.route('/model-inspector')
def model_inspector():
    """
    Halaman untuk menginspeksi model dan vektor
    """
    return render_template('model_inspector.html')

@public_bp.route('/thesaurus')
def thesaurus():
    """Public thesaurus page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    return render_template('thesaurus.html', user=user)

@public_bp.route('/thesaurus/browse')
def thesaurus_browse():
    """Public thesaurus browse page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    return render_template('thesaurus_browse.html', user=user)

@public_bp.route('/thesaurus/statistics')
def thesaurus_statistics():
    """Public thesaurus statistics page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    return render_template('thesaurus_statistics.html', user=user)

@public_bp.route('/thesaurus/word/<word>')
def thesaurus_word_detail(word):
    """Public thesaurus word detail page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    return render_template('thesaurus_detail.html', user=user, word=word)

@public_bp.route('/evaluasi')
def evaluasi():
    return render_template('evaluasi.html')

@public_bp.route('/search')
def search_main():
    """
    Halaman utama pencarian
    """
    return render_template('search_main.html')

@public_bp.route('/search/lexical')
def lexical_search():
    """
    Halaman pencarian lexical
    """
    return render_template('lexical_search.html')

@public_bp.route('/search/semantic')
def semantic_search():
    """
    Halaman pencarian semantic
    """
    return render_template('semantic_search.html')

@public_bp.route('/ontology/search')
def ontology_search():
    """
    Halaman pencarian ontology
    """
    return render_template('ontology_search.html') 

@public_bp.route('/ensemble-test')
def ensemble_test():
    """
    Halaman uji dan visualisasi model ensemble
    """
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('ensemble_test.html', user=user) 