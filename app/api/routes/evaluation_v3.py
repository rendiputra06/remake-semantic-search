from flask import Blueprint, request, jsonify
import time
from backend.db import get_relevant_verses_by_query, add_evaluation_result
from backend.lexical_search import LexicalSearch
from backend.thesaurus import IndonesianThesaurus
from app.api.services.search_service import SearchService
from backend.ensemble_embedding import EnsembleEmbeddingModel
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel

# Inisialisasi engine global
search_service = SearchService()
lexical_search_engine = None
thesaurus = None

# Cache untuk hasil pencarian (query_text, model_type, result_limit, threshold)
_search_cache = {}

def get_cached_search(query_text, model_type, result_limit, threshold):
    cache_key = (query_text, model_type, result_limit, threshold)
    return _search_cache.get(cache_key)

def set_cached_search(query_text, model_type, result_limit, threshold, results):
    cache_key = (query_text, model_type, result_limit, threshold)
    _search_cache[cache_key] = results

def init_lexical_search():
    global lexical_search_engine
    if lexical_search_engine is None:
        lexical_search_engine = LexicalSearch()
        lexical_search_engine.load_index()
    return lexical_search_engine

def init_thesaurus():
    global thesaurus
    if thesaurus is None:
        thesaurus = IndonesianThesaurus()
    return thesaurus

def extract_verse_ref(r):
    """
    Ekstrak referensi ayat dari hasil pencarian dalam format 'surah:ayat'.
    Mendukung beberapa variasi key.
    """
    if 'surah' in r and 'ayat' in r:
        return f"{r['surah']}:{r['ayat']}"
    elif 'surah_id' in r and 'verse_number' in r:
        return f"{r['surah_id']}:{r['verse_number']}"
    elif 'surah_number' in r and 'ayat_number' in r:
        return f"{r['surah_number']}:{r['ayat_number']}"
    return None

def calculate_metrics(found, ground_truth):
    """
    Hitung metrik evaluasi: true/false positive/negative, precision, recall, f1.
    """
    true_positive = len(found & ground_truth)
    false_positive = len(found - ground_truth)
    false_negative = len(ground_truth - found)
    true_negative = 0  # Tidak relevan untuk IR evaluation
    
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall + 1e-8) if (precision + recall) > 0 else 0
    
    # Additional metrics
    accuracy = (true_positive) / (true_positive + false_positive + false_negative) if (true_positive + false_positive + false_negative) > 0 else 0
    
    tp_verses = sorted(list(found & ground_truth))
    fp_verses = sorted(list(found - ground_truth))
    fn_verses = sorted(list(ground_truth - found))
    
    return {
        'true_positive': true_positive,
        'false_positive': false_positive,
        'false_negative': false_negative,
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
        'accuracy': round(accuracy, 4),
        'tp_verses': tp_verses,
        'fp_verses': fp_verses,
        'fn_verses': fn_verses
    }

def format_eval_result(method, label, found, ground_truth, exec_time, threshold=None, additional_info=None):
    """
    Format hasil evaluasi ke dalam dict standar.
    """
    metrics = calculate_metrics(found, ground_truth)
    result = {
        'method': method,
        'label': label,
        **metrics,
        'exec_time': exec_time,
        'threshold': threshold,
        'total_relevant': len(ground_truth),
        'total_found': len(found),
        'found_verses': sorted(list(found))
    }
    if additional_info:
        result.update(additional_info)
    return result

# Blueprint untuk evaluasi versi 3 (dengan konfigurasi ensemble lanjutan)
evaluation_v3_bp = Blueprint('evaluation_v3', __name__)

@evaluation_v3_bp.route('/<int:query_id>/run', methods=['POST'])
def run_evaluation_v3(query_id):
    """
    Jalankan evaluasi VERSI 3 dengan konfigurasi ensemble lanjutan.
    Mendukung:
    - Lexical dan semantic (word2vec, fasttext, glove, ensemble)
    - Konfigurasi bobot model ensemble (w2v_weight, ft_weight, glove_weight)
    - Konfigurasi voting bonus
    - Metode ensemble (weighted, voting, meta)
    - Threshold per model
    - Analisis perbandingan metode ensemble
    """
    data = request.json or {}
    result_limit = int(data.get('result_limit', 10))
    if result_limit == 0:
        result_limit = None  # None berarti tak terbatas
    
    # Ambil threshold per model (dict), fallback ke threshold global jika tidak ada
    threshold_per_model = data.get('threshold_per_model', {})
    def get_threshold(model):
        return float(threshold_per_model.get(model, 0.5))
    
    selected_methods = data.get('selected_methods', [])
    
    # Konfigurasi ensemble lanjutan
    ensemble_config = data.get('ensemble_config', {})
    w2v_threshold = float(ensemble_config.get('w2v_threshold', 0.5))
    ft_threshold = float(ensemble_config.get('ft_threshold', 0.5))
    glove_threshold = float(ensemble_config.get('glove_threshold', 0.5))
    voting_bonus = float(ensemble_config.get('voting_bonus', 0.05))
    ensemble_method = ensemble_config.get('method', 'weighted')  # weighted, voting, meta
    use_voting_filter = ensemble_config.get('use_voting_filter', False)
    
    # Ambil ground truth ayat relevan
    ayat_relevan = get_relevant_verses_by_query(query_id)
    ground_truth = set([a['verse_ref'] for a in ayat_relevan])
    if not ground_truth:
        return jsonify({'success': False, 'message': 'Ayat relevan belum diinput'}), 400

    # Ambil query text
    query_text = data.get('query_text', '')
    if not query_text:
        return jsonify({'success': False, 'message': 'Query text harus diisi'}), 400

    results = []
    ensemble_comparison = {}  # Untuk menyimpan perbandingan metode ensemble

    # --- 1. Evaluasi Lexical ---
    if not selected_methods or 'lexical' in selected_methods:
        try:
            start = time.time()
            found = get_cached_search(query_text, 'lexical', result_limit, 0.0)
            
            if found is None:
                search_engine = init_lexical_search()
                lexical_results = search_engine.search(query_text, exact_match=False, use_regex=False, limit=result_limit)
                found = set()
                for r in lexical_results if result_limit is None else lexical_results[:result_limit]:
                    ref = extract_verse_ref(r)
                    if ref:
                        found.add(ref)
                set_cached_search(query_text, 'lexical', result_limit, 0.0, found)
            
            exec_time = round(time.time() - start, 3)
            result = format_eval_result('lexical', 'Lexical', found, ground_truth, exec_time, threshold=0.0)
            # Simpan ke database
            add_evaluation_result(query_id, 'lexical', result['precision'], result['recall'], result['f1'], exec_time)
            results.append(result)
        except Exception as e:
            results.append({'method': 'lexical', 'label': 'Lexical', 'error': str(e)})

    # --- 2. Evaluasi Semantic (word2vec, fasttext, glove) ---
    for model in ['word2vec', 'fasttext', 'glove']:
        if not selected_methods or model in selected_methods:
            try:
                start = time.time()
                threshold = get_threshold(model)
                found = get_cached_search(query_text, model, result_limit, threshold)
                
                if found is None:
                    res = search_service.semantic_search(
                        query=query_text,
                        model_type=model,
                        limit=result_limit,
                        threshold=threshold,
                        user_id=None
                    )
                    found = set()
                    for r in res['results']:
                        ref = extract_verse_ref(r)
                        if ref:
                            found.add(ref)
                    set_cached_search(query_text, model, result_limit, threshold, found)
                
                exec_time = round(time.time() - start, 3)
                label = f'Semantic ({model.capitalize()})'
                result = format_eval_result(model, label, found, ground_truth, exec_time, threshold=threshold)
                # Simpan ke database
                add_evaluation_result(query_id, model, result['precision'], result['recall'], result['f1'], exec_time)
                results.append(result)
            except Exception as e:
                label = f'Semantic ({model.capitalize()})'
                results.append({'method': model, 'label': label, 'error': str(e)})

    # --- 3. Evaluasi Ensemble dengan Konfigurasi Lanjutan ---
    if not selected_methods or 'ensemble' in selected_methods:
        try:
            # Inisialisasi model-model dasar
            search_service._init_semantic_model('word2vec')
            search_service._init_semantic_model('fasttext')
            search_service._init_semantic_model('glove')
            
            w2v_model = search_service._semantic_models['word2vec']
            ft_model = search_service._semantic_models['fasttext']
            glove_model = search_service._semantic_models['glove']
            
            # Test berbagai konfigurasi ensemble
            ensemble_configs = []
            
            # Config 1: Weighted Averaging (now based on individual thresholds)
            if ensemble_method in ['weighted', 'all']:
                ensemble_configs.append({
                    'name': 'Weighted Averaging',
                    'method_key': 'ensemble_weighted',
                    'use_meta': False,
                    'use_voting_filter': use_voting_filter,
                    'thresholds': (w2v_threshold, ft_threshold, glove_threshold),
                    'voting_bonus': voting_bonus
                })
            
            # Config 2: Voting (fixed thresholds + voting bonus)
            if ensemble_method in ['voting', 'all']:
                ensemble_configs.append({
                    'name': 'Voting',
                    'method_key': 'ensemble_voting',
                    'use_meta': False,
                    'use_voting_filter': True,  # Voting always uses filter
                    'thresholds': (0.5, 0.5, 0.5), # Default for voting
                    'voting_bonus': voting_bonus
                })
            
            # Config 3: Meta-Ensemble (ML-based)
            if ensemble_method in ['meta', 'all']:
                ensemble_configs.append({
                    'name': 'Meta-Ensemble',
                    'method_key': 'ensemble_meta',
                    'use_meta': True,
                    'use_voting_filter': False,
                    'thresholds': (0.5, 0.5, 0.5),
                    'voting_bonus': 0.0
                })
            
            # Jalankan evaluasi untuk setiap konfigurasi
            for config in ensemble_configs:
                try:
                    start = time.time()
                    
                    # Buat instance ensemble dengan konfigurasi spesifik
                    ensemble = EnsembleEmbeddingModel(
                        w2v_model, ft_model, glove_model,
                        word2vec_threshold=config['thresholds'][0],
                        fasttext_threshold=config['thresholds'][1],
                        glove_threshold=config['thresholds'][2],
                        voting_bonus=config['voting_bonus'],
                        use_meta_ensemble=config['use_meta'],
                        use_voting_filter=config['use_voting_filter']
                    )
                    
                    # Lakukan pencarian
                    ensemble_results = ensemble.search(
                        query_text,
                        language='id',
                        limit=result_limit,
                        threshold=get_threshold('ensemble')
                    )
                    
                    found = set()
                    for r in ensemble_results:
                        ref = extract_verse_ref(r)
                        if ref:
                            found.add(ref)
                    
                    exec_time = round(time.time() - start, 3)
                    label = f'Ensemble ({config["name"]})'
                    
                    # Additional info untuk ensemble
                    ensemble_threshold = get_threshold('ensemble')
                    additional_info = {
                        'ensemble_method': config['name'],
                        'thresholds': {
                            'word2vec': config['thresholds'][0],
                            'fasttext': config['thresholds'][1],
                            'glove': config['thresholds'][2]
                        },
                        'voting_bonus': config['voting_bonus'],
                        'use_voting_filter': config['use_voting_filter']
                    }
                    
                    result = format_eval_result(
                        config['method_key'], 
                        label, 
                        found, 
                        ground_truth, 
                        exec_time,
                        threshold=ensemble_threshold,
                        additional_info=additional_info
                    )
                    
                    # Simpan ke database
                    add_evaluation_result(
                        query_id, 
                        config['method_key'], 
                        result['precision'], 
                        result['recall'], 
                        result['f1'], 
                        exec_time
                    )
                    
                    results.append(result)
                    ensemble_comparison[config['name']] = result
                    
                except Exception as e:
                    label = f'Ensemble ({config["name"]})'
                    results.append({'method': config['method_key'], 'label': label, 'error': str(e)})
                    
        except Exception as e:
            results.append({'method': 'ensemble', 'label': 'Ensemble', 'error': str(e)})

    # Analisis perbandingan ensemble
    ensemble_analysis = None
    if len(ensemble_comparison) > 1:
        ensemble_analysis = {
            'best_precision': max(ensemble_comparison.items(), key=lambda x: x[1].get('precision', 0)),
            'best_recall': max(ensemble_comparison.items(), key=lambda x: x[1].get('recall', 0)),
            'best_f1': max(ensemble_comparison.items(), key=lambda x: x[1].get('f1', 0)),
            'fastest': min(ensemble_comparison.items(), key=lambda x: x[1].get('exec_time', float('inf')))
        }

    return jsonify({
        'success': True, 
        'results': results,
        'ensemble_comparison': ensemble_comparison,
        'ensemble_analysis': ensemble_analysis,
        'config': {
            'query_text': query_text,
            'result_limit': result_limit,
            'ensemble_config': ensemble_config,
            'ground_truth_count': len(ground_truth)
        }
    })

@evaluation_v3_bp.route('/<int:query_id>/compare-thresholds', methods=['POST'])
def compare_thresholds(query_id):
    """
    Endpoint untuk membandingkan performa dengan berbagai threshold.
    Fitur tambahan untuk analisis sensitivitas threshold.
    """
    data = request.json or {}
    query_text = data.get('query_text', '')
    model_type = data.get('model_type', 'ensemble')
    threshold_range = data.get('threshold_range', [0.3, 0.4, 0.5, 0.6, 0.7])
    result_limit = data.get('result_limit', 10)
    
    if not query_text:
        return jsonify({'success': False, 'message': 'Query text harus diisi'}), 400
    
    # Ambil ground truth
    ayat_relevan = get_relevant_verses_by_query(query_id)
    ground_truth = set([a['verse_ref'] for a in ayat_relevan])
    if not ground_truth:
        return jsonify({'success': False, 'message': 'Ayat relevan belum diinput'}), 400
    
    comparison_results = []
    
    for threshold in threshold_range:
        try:
            start = time.time()
            res = search_service.semantic_search(
                query=query_text,
                model_type=model_type,
                limit=result_limit,
                threshold=threshold,
                user_id=None
            )
            
            found = set()
            for r in res['results']:
                ref = extract_verse_ref(r)
                if ref:
                    found.add(ref)
            
            exec_time = round(time.time() - start, 3)
            metrics = calculate_metrics(found, ground_truth)
            
            comparison_results.append({
                'threshold': threshold,
                'metrics': metrics,
                'exec_time': exec_time,
                'total_found': len(found)
            })
        except Exception as e:
            comparison_results.append({
                'threshold': threshold,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'model_type': model_type,
        'results': comparison_results
    })

@evaluation_v3_bp.route('/<int:query_id>/batch-evaluate', methods=['POST'])
def batch_evaluate(query_id):
    """
    Endpoint untuk evaluasi batch dengan berbagai kombinasi parameter.
    Fitur untuk eksperimen parameter tuning.
    """
    data = request.json or {}
    query_text = data.get('query_text', '')
    parameter_combinations = data.get('combinations', [])
    
    if not query_text:
        return jsonify({'success': False, 'message': 'Query text harus diisi'}), 400
    
    if not parameter_combinations:
        return jsonify({'success': False, 'message': 'Parameter combinations harus diisi'}), 400
    
    # Ambil ground truth
    ayat_relevan = get_relevant_verses_by_query(query_id)
    ground_truth = set([a['verse_ref'] for a in ayat_relevan])
    if not ground_truth:
        return jsonify({'success': False, 'message': 'Ayat relevan belum diinput'}), 400
    
    batch_results = []
    
    for idx, combo in enumerate(parameter_combinations):
        try:
            # Extract parameters
            w2v_w = combo.get('w2v_weight', 1.0)
            ft_w = combo.get('ft_weight', 1.0)
            glove_w = combo.get('glove_weight', 1.0)
            voting_b = combo.get('voting_bonus', 0.05)
            threshold = combo.get('threshold', 0.5)
            limit = combo.get('limit', 10)
            
            # Initialize models
            search_service._init_semantic_model('word2vec')
            search_service._init_semantic_model('fasttext')
            search_service._init_semantic_model('glove')
            
            w2v_model = search_service._semantic_models['word2vec']
            ft_model = search_service._semantic_models['fasttext']
            glove_model = search_service._semantic_models['glove']
            
            start = time.time()
            
            # Create ensemble with specific configuration
            ensemble = EnsembleEmbeddingModel(
                w2v_model, ft_model, glove_model,
                word2vec_weight=w2v_w,
                fasttext_weight=ft_w,
                glove_weight=glove_w,
                voting_bonus=voting_b,
                use_meta_ensemble=False,
                use_voting_filter=False
            )
            
            ensemble_results = ensemble.search(query_text, 'id', limit, threshold)
            
            found = set()
            for r in ensemble_results:
                ref = extract_verse_ref(r)
                if ref:
                    found.add(ref)
            
            exec_time = round(time.time() - start, 3)
            metrics = calculate_metrics(found, ground_truth)
            
            batch_results.append({
                'combination_id': idx,
                'parameters': combo,
                'metrics': metrics,
                'exec_time': exec_time,
                'total_found': len(found)
            })
            
        except Exception as e:
            batch_results.append({
                'combination_id': idx,
                'parameters': combo,
                'error': str(e)
            })
    
    # Find best combination
    valid_results = [r for r in batch_results if 'error' not in r]
    best_combination = None
    if valid_results:
        best_combination = max(valid_results, key=lambda x: x['metrics']['f1'])
    
    return jsonify({
        'success': True,
        'results': batch_results,
        'best_combination': best_combination,
        'total_combinations': len(parameter_combinations)
    })
