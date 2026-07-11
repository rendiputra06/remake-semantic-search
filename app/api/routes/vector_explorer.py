"""
API routes for the Vector Explorer feature.
Allows viewing/matching verse vectors.
"""
from flask import Blueprint, request, jsonify
from app.api.routes.search import search_service
from app.api.routes.playground import model_init_lock
from backend.preprocessing import preprocess_text
import numpy as np
import traceback

vector_explorer_bp = Blueprint('vector_explorer', __name__)

def get_word_vector_from_model(model, token, model_type):
    """Robust helper to extract a single word vector from any model, including ensemble."""
    if model_type == 'ensemble':
        v1 = get_word_vector_from_model(model.word2vec_model, token, 'word2vec')
        v2 = get_word_vector_from_model(model.fasttext_model, token, 'fasttext')
        v3 = get_word_vector_from_model(model.glove_model, token, 'glove')
        vectors = [v for v in [v1, v2, v3] if v is not None]
        if not vectors:
            return None
        return np.mean(vectors, axis=0)
    else:
        try:
            if hasattr(model.model, 'key_to_index') and token in model.model.key_to_index:
                return np.array(model.model[token]).flatten()
            elif hasattr(model.model, 'wv'):
                if token in model.model.wv:
                    return np.array(model.model.wv[token]).flatten()
            else:
                try:
                    return np.array(model.model[token]).flatten()
                except:
                    pass
        except Exception:
            pass
    return None

@vector_explorer_bp.route('/query', methods=['GET'])
def get_explorer_vectors():
    try:
        model_type = request.args.get('model_type', 'word2vec')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        match_word = request.args.get('match_word', '').strip()
        
        # 1. Initialize semantic model
        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400
            
        # Ensure ensemble base models are loaded
        if model_type == 'ensemble' and not model.verse_vectors:
            model.load_verse_vectors()
            
        verse_vectors = model.verse_vectors # dict of verse_id -> numpy array
        verse_data = model.verse_data # dict of verse_id -> dict info
        
        if not verse_vectors or not verse_data:
            return jsonify({'success': False, 'message': 'Vektor ayat belum dimuat di backend'}), 500
            
        # 2. If match_word is provided, calculate similarity scores
        word_vector = None
        word_vector_normalized = None
        similarity_scores = {}
        
        if match_word:
            word_tokens = preprocess_text(match_word)
            if word_tokens:
                word_vector = model._calculate_verse_vector(word_tokens)
                
            if word_vector is not None:
                # Convert to numpy array
                word_vector = np.array(word_vector).flatten()
                word_norm = np.linalg.norm(word_vector)
                if word_norm > 0:
                    word_vector_normalized = word_vector / word_norm
                else:
                    word_vector_normalized = word_vector
                
                # Calculate cosine similarity for all verses
                for verse_id, v_vec in verse_vectors.items():
                    v_vec = np.array(v_vec).flatten()
                    v_norm = np.linalg.norm(v_vec)
                    if word_norm > 0 and v_norm > 0:
                        sim = float(np.dot(word_vector, v_vec) / (word_norm * v_norm))
                    else:
                        sim = 0.0
                    similarity_scores[verse_id] = sim
            else:
                return jsonify({'success': False, 'message': f'Kata "{match_word}" tidak dikenali oleh model (OOV).'}), 400

        # 3. Filter and sort list of verses
        filtered_verse_ids = list(verse_data.keys())
        
        # Filter by search string (surah:ayat or text content)
        if search:
            search_lower = search.lower()
            filtered_verse_ids = [
                vid for vid in filtered_verse_ids
                if search_lower in vid.lower() or 
                   search_lower in verse_data[vid]['arabic'] or 
                   search_lower in verse_data[vid]['translation'].lower() or
                   search_lower in verse_data[vid]['surah_name'].lower()
            ]
            
        # Sort by similarity score if calculated, otherwise by default verse order (surah:ayat numerical order)
        if similarity_scores:
            filtered_verse_ids.sort(key=lambda vid: similarity_scores.get(vid, -1.0), reverse=True)
        else:
            # Natural sort order (e.g. 2:255)
            def natural_key(vid):
                parts = vid.split(':')
                return int(parts[0]), int(parts[1])
            filtered_verse_ids.sort(key=natural_key)
            
        # 4. Paginate
        total_verses = len(filtered_verse_ids)
        total_pages = (total_verses + limit - 1) // limit if total_verses > 0 else 1
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_verses)
        
        paginated_ids = filtered_verse_ids[start_idx:end_idx]
        
        # 5. Build results list
        results = []
        for vid in paginated_ids:
            v_info = verse_data[vid]
            v_vec = np.array(verse_vectors[vid]).flatten()
            v_norm = np.linalg.norm(v_vec)
            v_vec_normed = v_vec / v_norm if v_norm > 0 else v_vec
            
            item = {
                'verse_id': vid,
                'surah_number': v_info['surah_number'],
                'surah_name': v_info['surah_name'],
                'ayat_number': v_info['ayat_number'],
                'arabic': v_info['arabic'],
                'translation': v_info['translation'],
                'vector': v_vec_normed.tolist(),
            }
            if similarity_scores:
                item['similarity'] = similarity_scores[vid]
            results.append(item)
            
        return jsonify({
            'success': True,
            'data': results,
            'total_verses': total_verses,
            'total_pages': total_pages,
            'current_page': page,
            'limit': limit,
            'word_vector': word_vector_normalized.tolist() if word_vector_normalized is not None else None
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@vector_explorer_bp.route('/details', methods=['GET'])
def get_explorer_details():
    try:
        model_type = request.args.get('model_type', 'word2vec')
        verse_id = request.args.get('verse_id', '').strip()
        match_word = request.args.get('match_word', '').strip()
        
        if not verse_id:
            return jsonify({'success': False, 'message': 'Parameter verse_id diperlukan'}), 400
            
        # 1. Initialize semantic model
        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400
            
        if model_type == 'ensemble' and not model.verse_vectors:
            model.load_verse_vectors()
            
        verse_vectors = model.verse_vectors
        verse_data = model.verse_data
        
        if verse_id not in verse_data:
            return jsonify({'success': False, 'message': f'Ayat {verse_id} tidak ditemukan'}), 404
            
        v_info = verse_data[verse_id]
        v_vec = np.array(verse_vectors[verse_id]).flatten()
        v_norm = np.linalg.norm(v_vec)
        v_vec_normed = v_vec / v_norm if v_norm > 0 else v_vec
        
        # Preprocessing details
        raw_text = v_info['translation']
        lowercased = raw_text.lower()
        
        # Punctuation removal
        from backend.preprocessing import remove_punctuation, remove_stopwords
        no_punct = remove_punctuation(lowercased)
        tokens = no_punct.split()
        filtered_tokens = remove_stopwords(tokens)
        
        # Extract individual word vectors
        token_details = []
        token_vectors = []
        for t in filtered_tokens:
            vec = get_word_vector_from_model(model, t, model_type)
            if vec is not None:
                vec = np.array(vec).flatten()
                token_vectors.append(vec)
                token_details.append({
                    'token': t,
                    'is_oov': False,
                    'vector': vec.tolist()
                })
            else:
                token_details.append({
                    'token': t,
                    'is_oov': True,
                    'vector': None
                })
                
        # Mean Pooling calculation
        if token_vectors:
            mean_vec = np.mean(token_vectors, axis=0)
            mean_norm = np.linalg.norm(mean_vec)
            l2_vec = mean_vec / mean_norm if mean_norm > 0 else mean_vec
        else:
            mean_vec = np.zeros(200)
            l2_vec = np.zeros(200)
            
        # Get query word vector if match_word provided
        word_vector_normalized = None
        if match_word:
            word_tokens = preprocess_text(match_word)
            if word_tokens:
                word_vec = model._calculate_verse_vector(word_tokens)
                if word_vec is not None:
                    word_vec = np.array(word_vec).flatten()
                    w_norm = np.linalg.norm(word_vec)
                    word_vector_normalized = (word_vec / w_norm if w_norm > 0 else word_vec).tolist()
                    
        return jsonify({
            'success': True,
            'verse_id': verse_id,
            'surah_name': v_info['surah_name'],
            'surah_number': v_info['surah_number'],
            'ayat_number': v_info['ayat_number'],
            'arabic': v_info['arabic'],
            'translation': v_info['translation'],
            'preprocessing': {
                'lowercase': lowercased,
                'no_punctuation': no_punct,
                'tokens': tokens,
                'filtered_tokens': filtered_tokens
            },
            'token_details': token_details,
            'mean_vector': mean_vec.tolist(),
            'l2_vector': l2_vec.tolist(),
            'final_vector': v_vec_normed.tolist(),
            'final_vector_raw': v_vec.tolist(),
            'final_magnitude': float(v_norm),
            'match_word': match_word,
            'word_vector': word_vector_normalized
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
