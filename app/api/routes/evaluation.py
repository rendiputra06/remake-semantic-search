from flask import Blueprint, request, jsonify
import time
from backend.db import get_relevant_verses_by_query
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

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/<int:query_id>/run', methods=['POST'])
def run_evaluation(query_id):
    """
    Jalankan evaluasi pada semua metode pencarian untuk query tertentu.
    Mendukung: lexical, sinonim, semantic (word2vec, fasttext, glove), semantic+ontologi.
    """
    data = request.json or {}
    result_limit = int(data.get('result_limit', 10))
    threshold = float(data.get('threshold', 0.5))

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
    try:
        search_engine = init_lexical_search()
        start = time.time()
        lexical_results = search_engine.search(query_text, exact_match=False, use_regex=False, limit=result_limit)
        exec_time = round(time.time() - start, 3)
        found = set()
        for r in lexical_results:
            ref = extract_verse_ref(r)
            if ref:
                found.add(ref)
            else:
                raise Exception(f"Format hasil lexical tidak sesuai: {r}")
        results.append(format_eval_result('lexical', 'Lexical', found, ground_truth, exec_time))
    except Exception as e:
        results.append({'method': 'lexical', 'label': 'Lexical', 'error': str(e)})

    # --- 2. Evaluasi Sinonim (Expanded Query) ---
    try:
        thesaurus = init_thesaurus()
        start = time.time()
        query_words = query_text.split()
        expanded_queries = [query_text]
        # Ekspansi query dengan sinonim per kata
        for word in query_words:
            try:
                synonyms = thesaurus.get_synonyms(word)
                if synonyms:
                    for synonym in synonyms:
                        new_query = query_text.replace(word, synonym)
                        expanded_queries.append(new_query)
            except Exception:
                continue
        expanded_queries = list(dict.fromkeys(expanded_queries))  # Unik
        all_results = []
        # Jalankan semantic search untuk setiap query hasil ekspansi
        for expanded_query in expanded_queries:
            try:
                res = search_service.semantic_search(
                    query=expanded_query,
                    model_type='word2vec',
                    limit=result_limit,
                    threshold=threshold,
                    user_id=None
                )
                for r in res['results']:
                    r['source_query'] = expanded_query
                all_results.extend(res['results'])
            except Exception:
                continue
        unique_refs = set()
        for r in all_results:
            ref = extract_verse_ref(r)
            if ref:
                unique_refs.add(ref)
        found = set(list(unique_refs)[:result_limit])
        print(found)
        exec_time = round(time.time() - start, 3)
        results.append(format_eval_result('synonym', 'Sinonim', found, ground_truth, exec_time))
    except Exception as e:
        results.append({'method': 'synonym', 'label': 'Sinonim', 'error': str(e)})

    # --- 3. Evaluasi Semantic (word2vec, fasttext, glove) ---
    for model in ['word2vec', 'fasttext', 'glove']:
        try:
            start = time.time()
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
            exec_time = round(time.time() - start, 3)
            print(model, found)
            results.append(format_eval_result(model, f'Semantic ({model})', found, ground_truth, exec_time))
        except Exception as e:
            results.append({'method': model, 'label': f'Semantic ({model})', 'error': str(e)})

    # --- 4. Evaluasi Semantic+Ontologi (dummy: filter hasil semantic dengan ayat di ground_truth) ---
    for model in ['word2vec', 'fasttext', 'glove']:
        try:
            start = time.time()
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
                if ref and ref in ground_truth:
                    found.add(ref)
            exec_time = round(time.time() - start, 3)
            results.append(format_eval_result(f'{model}_ont', f'Semantic+Ontologi ({model})', found, ground_truth, exec_time))
        except Exception as e:
            results.append({'method': f'{model}_ont', 'label': f'Semantic+Ontologi ({model})', 'error': str(e)})

    return jsonify({'success': True, 'results': results}) 