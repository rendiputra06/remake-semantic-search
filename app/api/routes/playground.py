"""
API routes for the Data Playground feature with advanced analytical visualizers.
"""
import json
import io
import csv
import re
import traceback
from flask import Blueprint, request, jsonify, Response
from backend.preprocessing import remove_punctuation, remove_stopwords, tokenize
from app.api.routes.search import search_service
import numpy as np
from backend.db import get_verses_by_surah, get_surah_by_number
import threading

model_init_lock = threading.Lock()

playground_api_bp = Blueprint('playground_api', __name__)


def _extract_verse_vector(model, filtered_tokens):
    """Extract, mean-pool, and L2-normalize a verse vector from filtered tokens.

    Returns (norm_vec_list, magnitude, dimensions) tuple.
    norm_vec_list is a Python list of floats (all dimensions).
    Falls back to zero vector sized to model.vector_size when no tokens match.
    """
    # If it is ensemble model, delegate to its _calculate_query_vector method
    if hasattr(model, 'word2vec_model'):
        v_vec = model._calculate_query_vector(filtered_tokens)
        if v_vec is not None:
            norm_vec = np.array(v_vec).flatten()
            magnitude = float(np.linalg.norm(norm_vec))
            return norm_vec.tolist(), magnitude, len(norm_vec)
        else:
            # Determine dim from one of the sub-models
            dim = 200
            for sub_model in [model.word2vec_model, model.fasttext_model, model.glove_model]:
                try:
                    if hasattr(sub_model.model, 'vector_size'):
                        dim = sub_model.model.vector_size
                        break
                    elif hasattr(sub_model.model, 'wv') and hasattr(sub_model.model.wv, 'vector_size'):
                        dim = sub_model.model.wv.vector_size
                        break
                except:
                    continue
            return [0.0] * dim, 0.0, dim

    # Determine model dimension safely
    try:
        dim = model.model.vector_size
    except AttributeError:
        try:
            dim = model.model.wv.vector_size
        except AttributeError:
            dim = 200  # last-resort fallback

    word_vectors = []
    for token in filtered_tokens:
        vec = None
        try:
            if hasattr(model.model, 'key_to_index') and token in model.model.key_to_index:
                vec = model.model[token]
            elif hasattr(model.model, 'wv') and token in model.model.wv:
                vec = model.model.wv[token]
            else:
                try:
                    vec = model.model[token]
                except (KeyError, AttributeError):
                    pass
        except (KeyError, AttributeError):
            continue
        if vec is not None:
            word_vectors.append(np.array(vec).flatten())

    if word_vectors:
        mean_vec = np.mean(word_vectors, axis=0)
        norm = np.linalg.norm(mean_vec)
        norm_vec = (mean_vec if norm == 0 else mean_vec / norm)
        magnitude = float(norm)
        return norm_vec.tolist(), magnitude, len(norm_vec)
    else:
        return [0.0] * dim, 0.0, dim


def l2_normalize(vec):
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def calculate_weighted_query_vector(model, tokens, token_weights, model_type):
    word_vectors = []
    weights = []
    
    if model_type == 'ensemble':
        v1 = calculate_weighted_query_vector(model.word2vec_model, tokens, token_weights, 'word2vec')
        v2 = calculate_weighted_query_vector(model.fasttext_model, tokens, token_weights, 'fasttext')
        v3 = calculate_weighted_query_vector(model.glove_model, tokens, token_weights, 'glove')
        
        vectors = [np.array(v).flatten() for v in [v1, v2, v3] if v is not None]
        if not vectors:
            return None
        
        # Verify uniform shapes
        shapes = [v.shape for v in vectors]
        if not all(s == shapes[0] for s in shapes):
            vectors = [v for v in vectors if v.shape == shapes[0]]
            
        return l2_normalize(np.mean(vectors, axis=0))
        
    for token in tokens:
        weight = float(token_weights.get(token, 1.0))
        vec = None
        try:
            if hasattr(model.model, 'key_to_index') and token in model.model.key_to_index:
                vec = model.model[token]
            elif hasattr(model.model, 'wv'):
                if token in model.model.wv:
                    vec = model.model.wv[token]
            else:
                try:
                    vec = model.model[token]
                except:
                    pass
        except Exception:
            continue
            
        if vec is not None:
            word_vectors.append(np.array(vec).flatten())
            weights.append(weight)
            
    if not word_vectors:
        return None
        
    weighted_sum = np.zeros_like(word_vectors[0])
    total_weight = 0.0
    for vec, w in zip(word_vectors, weights):
        weighted_sum += vec * w
        total_weight += w
        
    if total_weight == 0:
        return None
        
    return l2_normalize(weighted_sum / total_weight)

@playground_api_bp.route('/run', methods=['POST'])
def run_playground():
    try:
        data = request.get_json() or {}
        query_text = data.get('query_text', '').strip()
        model_type = data.get('model_type', 'word2vec')
        token_weights = data.get('token_weights', {})
        model_weights = data.get('model_weights', {})
        
        if not query_text:
            return jsonify({'success': False, 'message': 'Kueri tidak boleh kosong'}), 400
            
        # 1. Preprocessing steps
        raw = query_text
        lowercased = query_text.lower()
        no_punct = remove_punctuation(lowercased)
        tokens = no_punct.split()
        filtered_tokens = remove_stopwords(tokens)
        
        # 2. Initialize and retrieve semantic model
        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400
            
        # 3. Compute Query Vector (Supporting custom Token Weighting)
        query_vector = calculate_weighted_query_vector(model, filtered_tokens, token_weights, model_type)
        
        if query_vector is None:
            return jsonify({'success': False, 'message': 'Kueri tidak mengandung kata yang dikenali oleh model (OOV)'}), 400
            
        # 4. Search and Similarity Calculation
        limit = int(data.get('limit', 100))
        
        # If ensemble model, calculate weighted similarity scores customly if model_weights is provided
        if model_type == 'ensemble' and model_weights:
            # Get base model search results with low thresholds
            w2v_res = {res['verse_id']: res for res in model.word2vec_model.search(query_text, 'id', limit=limit*3, threshold=model.word2vec_threshold)}
            ft_res = {res['verse_id']: res for res in model.fasttext_model.search(query_text, 'id', limit=limit*3, threshold=model.fasttext_threshold)}
            glove_res = {res['verse_id']: res for res in model.glove_model.search(query_text, 'id', limit=limit*3, threshold=model.glove_threshold)}
            
            all_vids = set(w2v_res.keys()) | set(ft_res.keys()) | set(glove_res.keys())
            
            aggregation_method = data.get('aggregation_method', 'score_fusion')
            results = []
            
            if aggregation_method == 'rank_fusion':
                w2v_ranked = sorted(w2v_res.values(), key=lambda x: x['similarity'], reverse=True)
                ft_ranked = sorted(ft_res.values(), key=lambda x: x['similarity'], reverse=True)
                glove_ranked = sorted(glove_res.values(), key=lambda x: x['similarity'], reverse=True)
                
                w2v_ranks = {res['verse_id']: idx for idx, res in enumerate(w2v_ranked)}
                ft_ranks = {res['verse_id']: idx for idx, res in enumerate(ft_ranked)}
                glove_ranks = {res['verse_id']: idx for idx, res in enumerate(glove_ranked)}
                
                max_rank = limit * 3
                for vid in all_vids:
                    info = w2v_res.get(vid) or ft_res.get(vid) or glove_res.get(vid)
                    if not info:
                        continue
                    
                    w2v_sim = w2v_res.get(vid, {}).get('similarity', 0.0)
                    ft_sim = ft_res.get(vid, {}).get('similarity', 0.0)
                    glove_sim = glove_res.get(vid, {}).get('similarity', 0.0)
                    
                    score = 0.0
                    models_found = 0
                    if vid in w2v_ranks:
                        score += float(model_weights.get('word2vec', 1.0)) * (max_rank - w2v_ranks[vid])
                        models_found += 1
                    if vid in ft_ranks:
                        score += float(model_weights.get('fasttext', 1.0)) * (max_rank - ft_ranks[vid])
                        models_found += 1
                    if vid in glove_ranks:
                        score += float(model_weights.get('glove', 1.0)) * (max_rank - glove_ranks[vid])
                        models_found += 1
                    
                    max_possible_score = max_rank * (float(model_weights.get('word2vec', 1.0)) + float(model_weights.get('fasttext', 1.0)) + float(model_weights.get('glove', 1.0)))
                    normalized_score = score / max_possible_score if max_possible_score > 0 else 0.0
                    
                    results.append({
                        'verse_id': vid,
                        'surah_number': info['surah_number'],
                        'surah_name': info['surah_name'],
                        'ayat_number': info['ayat_number'],
                        'arabic': info['arabic'],
                        'translation': info['translation'],
                        'similarity': normalized_score,
                        'individual_scores': {
                            'word2vec': w2v_sim,
                            'fasttext': ft_sim,
                            'glove': glove_sim
                        },
                        'model_count': models_found
                    })
            elif aggregation_method == 'concatenation':
                w2v_w = float(model_weights.get('word2vec', 1.0))
                ft_w = float(model_weights.get('fasttext', 1.0))
                glove_w = float(model_weights.get('glove', 1.0))
                
                norm_factor = np.sqrt(w2v_w**2 + ft_w**2 + glove_w**2) * np.sqrt(3.0)
                for vid in all_vids:
                    info = w2v_res.get(vid) or ft_res.get(vid) or glove_res.get(vid)
                    if not info:
                        continue
                    
                    w2v_sim = w2v_res.get(vid, {}).get('similarity', 0.0)
                    ft_sim = ft_res.get(vid, {}).get('similarity', 0.0)
                    glove_sim = glove_res.get(vid, {}).get('similarity', 0.0)
                    
                    dot_product = (w2v_w * w2v_sim) + (ft_w * ft_sim) + (glove_w * glove_sim)
                    concat_sim = dot_product / norm_factor if norm_factor > 0 else 0.0
                    
                    model_count = sum([1 for s in [w2v_sim, ft_sim, glove_sim] if s > 0])
                    
                    results.append({
                        'verse_id': vid,
                        'surah_number': info['surah_number'],
                        'surah_name': info['surah_name'],
                        'ayat_number': info['ayat_number'],
                        'arabic': info['arabic'],
                        'translation': info['translation'],
                        'similarity': concat_sim,
                        'individual_scores': {
                            'word2vec': w2v_sim,
                            'fasttext': ft_sim,
                            'glove': glove_sim
                        },
                        'model_count': model_count
                    })
            else: # score_fusion
                for vid in all_vids:
                    info = w2v_res.get(vid) or ft_res.get(vid) or glove_res.get(vid)
                    if not info:
                        continue
                    
                    w2v_sim = w2v_res.get(vid, {}).get('similarity', 0.0)
                    ft_sim = ft_res.get(vid, {}).get('similarity', 0.0)
                    glove_sim = glove_res.get(vid, {}).get('similarity', 0.0)
                    
                    sims = []
                    weights = []
                    if w2v_sim > 0:
                        sims.append(w2v_sim)
                        weights.append(float(model_weights.get('word2vec', 1.0)))
                    if ft_sim > 0:
                        sims.append(ft_sim)
                        weights.append(float(model_weights.get('fasttext', 1.0)))
                    if glove_sim > 0:
                        sims.append(glove_sim)
                        weights.append(float(model_weights.get('glove', 1.0)))
                        
                    if not sims:
                        continue
                        
                    ensemble_score = sum(s * w for s, w in zip(sims, weights)) / sum(weights)
                    
                    model_count = len(sims)
                    if model_count >= 2:
                        ensemble_score += model.voting_bonus
                        
                    results.append({
                        'verse_id': vid,
                        'surah_number': info['surah_number'],
                        'surah_name': info['surah_name'],
                        'ayat_number': info['ayat_number'],
                        'arabic': info['arabic'],
                        'translation': info['translation'],
                        'similarity': ensemble_score,
                        'individual_scores': {
                            'word2vec': w2v_sim,
                            'fasttext': ft_sim,
                            'glove': glove_sim
                        },
                        'model_count': model_count
                    })
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:limit]
        else:
            # Fallback to standard search
            results = model.search(query_text, language='id', limit=limit, threshold=0.0)
            
        # Add the actual verse vectors to the results returned to frontend
        for r in results:
            vid = r['verse_id']
            v_vec = model.verse_vectors.get(vid)
            if v_vec is not None:
                r['vector_values'] = np.array(v_vec).flatten().tolist()
            
        # 5. Compute SVD projection coordinates for 2D visualization (Top 10 verses + Query)
        pca_coords = []
        if len(results) > 0:
            q_vec_1d = np.array(query_vector).flatten()
            vectors = [q_vec_1d.tolist()]
            labels = ["Kueri"]
            types = ["query"]
            
            for r in results[:10]:
                vid = r['verse_id']
                v_vec = model.verse_vectors.get(vid)
                if v_vec is not None:
                    v_vec_1d = np.array(v_vec).flatten()
                    vectors.append(v_vec_1d.tolist())
                    labels.append(f"{r['surah_number']}:{r['ayat_number']}")
                    types.append("verse")
                    
            if len(vectors) >= 3:
                shapes = [len(v) for v in vectors]
                if all(s == shapes[0] for s in shapes):
                    X = np.array(vectors)
                    X_centered = X - np.mean(X, axis=0)
                    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
                    X_2d = U[:, :2] * S[:2]
                    
                    for i, coord in enumerate(X_2d.tolist()):
                        pca_coords.append({
                            "label": labels[i],
                            "x": float(coord[0]),
                            "y": float(coord[1]),
                            "type": types[i]
                        })
        
        # For ensemble, retrieve sub-model vectors to display to the user
        ensemble_sub_vectors = None
        if model_type == 'ensemble':
            w2v_v = calculate_weighted_query_vector(model.word2vec_model, filtered_tokens, token_weights, 'word2vec')
            ft_v = calculate_weighted_query_vector(model.fasttext_model, filtered_tokens, token_weights, 'fasttext')
            glove_v = calculate_weighted_query_vector(model.glove_model, filtered_tokens, token_weights, 'glove')
            ensemble_sub_vectors = {
                'word2vec': w2v_v.tolist() if w2v_v is not None else None,
                'fasttext': ft_v.tolist() if ft_v is not None else None,
                'glove': glove_v.tolist() if glove_v is not None else None,
            }

        return jsonify({
            'success': True,
            'preprocessing': {
                'raw': raw,
                'lowercased': lowercased,
                'no_punctuation': no_punct,
                'tokens': tokens,
                'filtered_tokens': filtered_tokens
            },
            'vector': {
                'dimensions': len(query_vector),
                'magnitude': float(np.linalg.norm(query_vector)),
                'values': query_vector.tolist()
            },
            'ensemble_sub_vectors': ensemble_sub_vectors,
            'results': results,
            'pca': pca_coords
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@playground_api_bp.route('/neighbors', methods=['GET'])
def get_neighbors():
    try:
        word = request.args.get('word', '').strip().lower()
        model_type = request.args.get('model_type', 'word2vec')
        
        if not word:
            return jsonify({'success': False, 'message': 'Kata tidak boleh kosong'}), 400
            
        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400
            
        similar_words = []
        if model_type == 'ensemble':
            # Ensemble neighbors combinations
            w2v_sim = []
            ft_sim = []
            glove_sim = []
            
            try:
                if hasattr(model.word2vec_model.model, 'wv') and word in model.word2vec_model.model.wv:
                    w2v_sim = model.word2vec_model.model.wv.most_similar(word, topn=20)
                elif word in model.word2vec_model.model:
                    w2v_sim = model.word2vec_model.model.most_similar(word, topn=20)
            except:
                pass
                
            try:
                if hasattr(model.fasttext_model.model, 'wv') and word in model.fasttext_model.model.wv:
                    ft_sim = model.fasttext_model.model.wv.most_similar(word, topn=20)
                elif word in model.fasttext_model.model:
                    ft_sim = model.fasttext_model.model.most_similar(word, topn=20)
            except:
                pass
                
            try:
                if word in model.glove_model.model:
                    glove_sim = model.glove_model.model.most_similar(word, topn=20)
            except:
                pass
                
            merged = {}
            for w, s in w2v_sim + ft_sim + glove_sim:
                if w not in merged:
                    merged[w] = []
                merged[w].append(s)
                
            sorted_merged = sorted(
                [(w, float(np.mean(scores))) for w, scores in merged.items()],
                key=lambda x: x[1],
                reverse=True
            )
            similar_words = sorted_merged[:10]
        else:
            try:
                if hasattr(model.model, 'wv') and word in model.model.wv:
                    similar_words = model.model.wv.most_similar(word, topn=10)
                elif word in model.model:
                    similar_words = model.model.most_similar(word, topn=10)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Kata "{word}" tidak terdaftar dalam model vokabulari.'}), 400
                
        # Format output
        data = [{"word": w, "similarity": float(s)} for w, s in similar_words]
        return jsonify({
            'success': True,
            'word': word,
            'neighbors': data
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@playground_api_bp.route('/indexing/simulate', methods=['POST'])
def run_indexing_simulation():
    try:
        data = request.get_json() or {}
        try:
            surah_number = int(data.get('surah_number', 1))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Nomor surah harus berupa angka'}), 400
        model_type = data.get('model_type', 'word2vec')
        
        # 1. Fetch surah details & verses
        surah = get_surah_by_number(surah_number)
        if not surah:
            return jsonify({'success': False, 'message': f'Surah dengan nomor {surah_number} tidak ditemukan'}), 404
            
        verses = get_verses_by_surah(surah_number)
        
        # 2. Init model safely using lock
        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400
            
        response_data = []
        for v in verses:
            raw_trans = v.get('verse_translation') or ''

            # Preprocessing trace
            lowercased = raw_trans.lower()
            no_punct = remove_punctuation(lowercased)
            tokens = no_punct.split()
            filtered_tokens = remove_stopwords(tokens)

            # Vector extraction (shared helper — no bare except, no duplication)
            values_full, magnitude, dimensions = _extract_verse_vector(model, filtered_tokens)
            values_preview = values_full[:10]

            # SQLite payload preview
            verse_ref = f"{v['surah_id']}:{v['verse_number']}"
            db_query = "INSERT INTO verse_vectors (verse_id, model_type, vector_blob) VALUES (?, ?, ?)"
            db_params = [verse_ref, model_type, f"<BLOB {dimensions * 4} bytes>"]

            response_data.append({
                'verse_number': v['verse_number'],
                'arabic': v['verse_text'],
                'raw_translation': raw_trans,
                'preprocessing_steps': {
                    'lowercase': lowercased,
                    'no_punctuation': no_punct,
                    'tokens': tokens,
                    'filtered_tokens': filtered_tokens
                },
                'vector': {
                    'dimensions': dimensions,
                    'magnitude': magnitude,
                    'values_preview': values_preview,
                    'values_full': values_full
                },
                'sqlite_payload': {
                    'query': db_query,
                    'params': db_params
                }
            })

        return jsonify({
            'success': True,
            'surah_name': surah['surah_name'],
            'data': response_data
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@playground_api_bp.route('/indexing/download', methods=['POST'])
def download_indexing_vectors():
    """Download semua vektor surah dalam format JSON atau CSV."""
    try:
        data = request.get_json() or {}
        try:
            surah_number = int(data.get('surah_number', 1))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Nomor surah harus berupa angka'}), 400
        model_type = data.get('model_type', 'word2vec')
        fmt = data.get('format', 'json').lower()  # 'json' or 'csv'

        surah = get_surah_by_number(surah_number)
        if not surah:
            return jsonify({'success': False, 'message': 'Surah tidak ditemukan'}), 404

        verses = get_verses_by_surah(surah_number)

        with model_init_lock:
            search_service._init_semantic_model(model_type)
        model = search_service._semantic_models.get(model_type)
        if not model:
            return jsonify({'success': False, 'message': f'Model {model_type} tidak ditemukan'}), 400

        records = []
        for v in verses:
            raw_trans = v.get('verse_translation') or ''
            lowercased = raw_trans.lower()
            no_punct = remove_punctuation(lowercased)
            tokens = no_punct.split()
            filtered_tokens = remove_stopwords(tokens)

            # Use shared helper — no duplication, no bare except, no hardcoded dim
            norm_vec, magnitude, dimensions = _extract_verse_vector(model, filtered_tokens)

            verse_ref = f"{v['surah_id']}:{v['verse_number']}"
            records.append({
                'verse_ref': verse_ref,
                'surah_name': surah['surah_name'],
                'verse_number': v['verse_number'],
                'model_type': model_type,
                'magnitude': magnitude,
                'dimensions': dimensions,
                'vector': norm_vec
            })

        # Sanitize filename — strip chars illegal on Windows/macOS/Linux
        safe_name = re.sub(r'[^\w\-]', '_', surah['surah_name'])
        filename_base = f"vectors_{safe_name}_{model_type}"

        if fmt == 'csv':
            output = io.StringIO()
            if records:
                dims = len(records[0]['vector'])
                fieldnames = (
                    ['verse_ref', 'surah_name', 'verse_number', 'model_type', 'magnitude', 'dimensions']
                    + [f'dim_{i+1}' for i in range(dims)]
                )
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    row = {k: val for k, val in r.items() if k != 'vector'}
                    for i, val in enumerate(r['vector']):
                        row[f'dim_{i+1}'] = round(val, 8)
                    writer.writerow(row)
            content = output.getvalue()
            return Response(
                content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename_base}.csv'}
            )
        else:  # json
            content = json.dumps({
                'surah_name': surah['surah_name'],
                'surah_number': surah_number,
                'model_type': model_type,
                'total_verses': len(records),
                'vectors': records
            }, ensure_ascii=False, indent=2)
            return Response(
                content,
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename={filename_base}.json'}
            )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
