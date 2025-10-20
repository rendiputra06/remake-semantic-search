from flask import Blueprint, request, jsonify
import time
from backend.db import get_relevant_verses_by_query, add_evaluation_result
from backend.lexical_search import LexicalSearch
from backend.thesaurus import IndonesianThesaurus
from app.api.services.search_service import SearchService

# Inisialisasi engine global
search_service = SearchService()
lexical_search_engine = None
thesaurus = None

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
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall + 1e-8) if (precision + recall) > 0 else 0
    return {
        'true_positive': true_positive,
        'false_positive': false_positive,
        'false_negative': false_negative,
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3)
    }

def format_eval_result(method, label, found, ground_truth, exec_time):
    """
    Format hasil evaluasi ke dalam dict standar.
    """
    metrics = calculate_metrics(found, ground_truth)
    return {
        'method': method,
        'label': label,
        **metrics,
        'exec_time': exec_time,
        'total_relevant': len(ground_truth),
        'total_found': len(found),
        'found_verses': sorted(list(found))
    }

# Blueprint untuk evaluasi versi 2 (tanpa ontologi)
evaluation_v2_bp = Blueprint('evaluation_v2', __name__)

@evaluation_v2_bp.route('/<int:query_id>/run', methods=['POST'])
def run_evaluation_v2(query_id):
    """
    Jalankan evaluasi VERSI 2 pada semua metode pencarian untuk query tertentu.
    HANYA mendukung: lexical dan semantic (word2vec, fasttext, glove, ensemble).
    TANPA ontologi models.
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

    # Ambil ground truth ayat relevan
    ayat_relevan = get_relevant_verses_by_query(query_id)
    ground_truth = set([a['verse_ref'] for a in ayat_relevan])
    if not ground_truth:
        return jsonify({'success': False, 'message': 'Ayat relevan belum diinput'}), 400

    # Ambil query text (sementara: input manual dari frontend)
    query_text = data.get('query_text', '')
    if not query_text:
        return jsonify({'success': False, 'message': 'Query text harus diisi'}), 400

    results = []

    # --- 1. Evaluasi Lexical ---
    if not selected_methods or 'lexical' in selected_methods:
        try:
            search_engine = init_lexical_search()
            start = time.time()
            lexical_results = search_engine.search(query_text, exact_match=False, use_regex=False, limit=result_limit)
            # Jika result_limit None, jangan slice hasil
            if result_limit is None:
                found = set()
                for r in lexical_results:
                    ref = extract_verse_ref(r)
                    if ref:
                        found.add(ref)
                    else:
                        raise Exception(f"Format hasil lexical tidak sesuai: {r}")
            else:
                found = set()
                for r in lexical_results[:result_limit]:
                    ref = extract_verse_ref(r)
                    if ref:
                        found.add(ref)
                    else:
                        raise Exception(f"Format hasil lexical tidak sesuai: {r}")
            exec_time = round(time.time() - start, 3)
            result = format_eval_result('lexical', 'Lexical', found, ground_truth, exec_time)
            # Simpan ke database
            add_evaluation_result(query_id, 'lexical', result['precision'], result['recall'], result['f1'], exec_time)
            results.append(result)
        except Exception as e:
            results.append({'method': 'lexical', 'label': 'Lexical', 'error': str(e)})

    # --- 2. Evaluasi Semantic (word2vec, fasttext, glove, ensemble) ---
    for model in ['word2vec', 'fasttext', 'glove', 'ensemble']:
        if not selected_methods or model in selected_methods:
            try:
                start = time.time()
                res = search_service.semantic_search(
                    query=query_text,
                    model_type=model,
                    limit=result_limit,
                    threshold=get_threshold(model),
                    user_id=None
                )
                if result_limit is None:
                    found = set()
                    for r in res['results']:
                        ref = extract_verse_ref(r)
                        if ref:
                            found.add(ref)
                else:
                    found = set()
                    for r in res['results'][:result_limit]:
                        ref = extract_verse_ref(r)
                        if ref:
                            found.add(ref)
                exec_time = round(time.time() - start, 3)
                label = f'Semantic ({model})' if model != 'ensemble' else 'Semantic (Ensemble)'
                result = format_eval_result(model, label, found, ground_truth, exec_time)
                # Simpan ke database
                add_evaluation_result(query_id, model, result['precision'], result['recall'], result['f1'], exec_time)
                results.append(result)
            except Exception as e:
                label = f'Semantic ({model})' if model != 'ensemble' else 'Semantic (Ensemble)'
                results.append({'method': model, 'label': label, 'error': str(e)})

    return jsonify({'success': True, 'results': results})
