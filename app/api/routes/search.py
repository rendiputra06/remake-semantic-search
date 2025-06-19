"""
Search related routes for the semantic search API.
"""
from flask import Blueprint, request, session
from backend.db import get_db_connection, add_search_history, get_user_settings
from backend.db import update_app_statistics
from backend.lexical_search import LexicalSearch
from backend.thesaurus import IndonesianThesaurus
from ..services.search_service import SearchService
from ..utils import create_response, error_response
import json
import traceback

search_bp = Blueprint('search', __name__)

# Global instances
search_service = SearchService()
lexical_search_engine = None
thesaurus = None

def init_lexical_search():
    """
    Inisialisasi pencarian leksikal
    """
    global lexical_search_engine
    if lexical_search_engine is None:
        try:
            lexical_search_engine = LexicalSearch()
            lexical_search_engine.load_index()
            return lexical_search_engine
        except Exception as e:
            raise Exception(f'Gagal menginisialisasi pencarian leksikal: {str(e)}')
    return lexical_search_engine

@search_bp.route('/search', methods=['POST'])
def search():
    """
    Endpoint untuk pencarian semantik
    """
    try:
        # Get data from JSON request
        data = request.get_json()
        if not data:
            return error_response(400, 'Data tidak diberikan dalam format JSON')
        
        query = data.get('query', '').strip()
        model_type = data.get('model', 'word2vec')
        result_limit = int(data.get('limit', 10))
        threshold = float(data.get('threshold', 0.5))
        
        if not query:
            return error_response(400, 'Query tidak boleh kosong')
        
        # Validasi model_type
        if model_type not in ['word2vec', 'fasttext', 'glove', 'ensemble']:
            return error_response(400, f"Model '{model_type}' tidak didukung")
        
        try:
            # Menggunakan semantic_search dari SearchService
            results = search_service.semantic_search(
                query=query,
                model_type=model_type,
                limit=result_limit,
                threshold=threshold,
                user_id=session.get('user_id')
            )
            
            return create_response(
                data=results,
                message='Pencarian berhasil'
            )
            
        except Exception as e:
            error_msg = str(e)
            if "Model belum dimuat" in error_msg:
                # Coba inisialisasi ulang model
                try:
                    search_service._init_semantic_model(model_type)
                    # Coba pencarian lagi
                    results = search_service.semantic_search(
                        query=query,
                        model_type=model_type,
                        limit=result_limit,
                        threshold=threshold,
                        user_id=session.get('user_id')
                    )
                    return create_response(
                        data=results,
                        message='Pencarian berhasil'
                    )
                except Exception as retry_error:
                    return error_response(500, f"Gagal memuat model: {str(retry_error)}")
            return error_response(500, error_msg)
        
    except Exception as e:
        traceback.print_exc()
        return error_response(500, str(e))

@search_bp.route('/search/lexical', methods=['POST'])
def lexical_search():
    """
    Endpoint untuk pencarian leksikal
    """
    try:
        # Get data from JSON request
        data = request.get_json()
        if not data:
            return error_response(400, 'Data tidak diberikan dalam format JSON')
        
        query = data.get('query', '').strip()
        exact_match = data.get('exact_match', False)
        use_regex = data.get('use_regex', False)
        limit = int(data.get('limit', 10))
        
        if not query:
            return error_response(400, 'Query tidak boleh kosong')
        
        # Initialize lexical search if needed
        try:
            search_engine = init_lexical_search()
        except Exception as e:
            return error_response(500, f'Gagal menginisialisasi pencarian leksikal: {str(e)}')
        
        # Execute search
        try:
            results = search_engine.search(
                query,
                exact_match=exact_match,
                use_regex=use_regex,
                limit=limit
            )
        except Exception as e:
            return error_response(500, f'Error saat melakukan pencarian: {str(e)}')
        
        # Add to search history if user is logged in
        if 'user_id' in session:
            add_search_history(session['user_id'], query, 'lexical', len(results))
            update_app_statistics('lexical_searches', len(results))
        
        return create_response(
            data={
                'query': query,
                'search_type': 'lexical',
                'exact_match': exact_match,
                'use_regex': use_regex,
                'results': results,
                'count': len(results)
            },
            message='Pencarian berhasil'
        )
        
    except Exception as e:
        traceback.print_exc()
        return error_response(500, str(e))

@search_bp.route('/search/expanded', methods=['POST'])
def expanded_search():
    """
    Endpoint untuk pencarian leksikal dengan ekspansi query menggunakan sinonim
    """
    try:
        # Get data from JSON request
        data = request.get_json()
        if not data:
            return error_response(400, 'Data tidak diberikan dalam format JSON')
        
        query = data.get('query', '').strip()
        model_type = data.get('model', 'word2vec')
        result_limit = int(data.get('limit', 10))
        threshold = float(data.get('threshold', 0.5))
        
        if not query:
            return error_response(400, 'Query tidak boleh kosong')
        
        # Initialize thesaurus if needed
        global thesaurus
        if thesaurus is None:
            try:
                thesaurus = IndonesianThesaurus()
            except Exception as e:
                return error_response(500, f'Gagal menginisialisasi tesaurus: {str(e)}')
        
        # Get synonyms for query words
        query_words = query.split()
        expanded_queries = [query]  # Original query is always included
        
        for word in query_words:
            try:
                synonyms = thesaurus.get_synonyms(word)
                if synonyms:
                    # Create new queries with each synonym
                    for synonym in synonyms:
                        new_query = query.replace(word, synonym)
                        expanded_queries.append(new_query)
            except Exception as e:
                print(f"Error getting synonyms for {word}: {str(e)}")
                continue
        
        # Remove duplicates while preserving order
        expanded_queries = list(dict.fromkeys(expanded_queries))
        
        # Search with each expanded query using SearchService
        all_results = []
        for expanded_query in expanded_queries:
            try:
                # Gunakan semantic_search dari SearchService
                results = search_service.semantic_search(
                    query=expanded_query,
                    model_type=model_type,
                    limit=result_limit,
                    threshold=threshold,
                    user_id=session.get('user_id')
                )
                
                # Tambahkan source query ke setiap hasil
                for result in results['results']:
                    result['source_query'] = expanded_query
                all_results.extend(results['results'])
                
            except Exception as e:
                print(f"Error searching with query '{expanded_query}': {str(e)}")
                continue
        
        # Remove duplicates based on verse_id while keeping highest similarity
        unique_results = {}
        for result in all_results:
            verse_id = result['verse_id']
            if verse_id not in unique_results or result['similarity'] > unique_results[verse_id]['similarity']:
                unique_results[verse_id] = result
        
        results = list(unique_results.values())
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:result_limit]
        
        # Add classification information
        results = search_service._enhance_results_with_classification(results)
        
        # Add to search history if user is logged in
        if 'user_id' in session:
            add_search_history(session['user_id'], query, 'expanded', len(results))
            update_app_statistics(
                searches=1,
                users=1,
                model=model_type,
                avg_results=len(results)
            )
        
        return create_response(
            data={
                'query': query,
                'model': model_type,
                'search_type': 'expanded',
                'expanded_queries': expanded_queries,
                'results': results,
                'count': len(results)
            },
            message='Pencarian berhasil'
        )
        
    except Exception as e:
        traceback.print_exc()
        return error_response(500, str(e))

@search_bp.route('/search/distribution', methods=['POST'])
def search_distribution():
    """
    Endpoint untuk mendapatkan distribusi hasil pencarian berdasarkan kategori
    """
    try:
        results = request.get_json()
        if not results:
            return error_response(400, 'Data hasil pencarian tidak diberikan')
        
        distribution = {}
        # ... distribution calculation ...
        
        return create_response(
            data=distribution,
            message='Distribusi berhasil dihitung'
        )
        
    except Exception as e:
        return error_response(500, str(e))