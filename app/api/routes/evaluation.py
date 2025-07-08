from flask import Blueprint, request, jsonify
import time
from backend.db import get_relevant_verses_by_query, add_evaluation_result
from backend.lexical_search import LexicalSearch
from backend.thesaurus import IndonesianThesaurus
from app.api.services.search_service import SearchService
from app.api.services.ontology_service import OntologyService

# Inisialisasi engine global
search_service = SearchService()
lexical_search_engine = None
thesaurus = None
ontology_service = OntologyService(storage_type='database')

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
            exec_time = round(time.time() - start, 3)
            found = set()
            for r in lexical_results:
                ref = extract_verse_ref(r)
                if ref:
                    found.add(ref)
                else:
                    raise Exception(f"Format hasil lexical tidak sesuai: {r}")
            result = format_eval_result('lexical', 'Lexical', found, ground_truth, exec_time)
            # Simpan ke database
            add_evaluation_result(query_id, 'lexical', result['precision'], result['recall'], result['f1'], exec_time)
            results.append(result)
        except Exception as e:
            results.append({'method': 'lexical', 'label': 'Lexical', 'error': str(e)})

    # --- 2. Evaluasi Sinonim (Expanded Query) ---
    if not selected_methods or 'synonym' in selected_methods:
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
            exec_time = round(time.time() - start, 3)
            result = format_eval_result('synonym', 'Sinonim', found, ground_truth, exec_time)
            # Simpan ke database
            add_evaluation_result(query_id, 'synonym', result['precision'], result['recall'], result['f1'], exec_time)
            results.append(result)
        except Exception as e:
            results.append({'method': 'synonym', 'label': 'Sinonim', 'error': str(e)})

    # --- 3. Evaluasi Semantic (word2vec, fasttext, glove, ensemble) ---
    for model in ['word2vec', 'fasttext', 'glove', 'ensemble']:
        if not selected_methods or model in selected_methods:
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
                label = f'Semantic ({model})' if model != 'ensemble' else 'Semantic (Ensemble)'
                result = format_eval_result(model, label, found, ground_truth, exec_time)
                # Simpan ke database
                add_evaluation_result(query_id, model, result['precision'], result['recall'], result['f1'], exec_time)
                results.append(result)
            except Exception as e:
                label = f'Semantic ({model})' if model != 'ensemble' else 'Semantic (Ensemble)'
                results.append({'method': model, 'label': label, 'error': str(e)})

    # --- 4. Evaluasi Semantic+Ontologi (per model) ---
    ontology_model_map = {
        'ontology_word2vec': 'word2vec',
        'ontology_fasttext': 'fasttext',
        'ontology_glove': 'glove',
        'ontology_ensemble': 'ensemble',
    }
    for ont_key, model in ontology_model_map.items():
        if not selected_methods or ont_key in selected_methods:
            try:
                start = time.time()
                # Ekspansi query dengan ontologi
                main_concept = ontology_service.find_concept(query_text)
                expanded_queries = [query_text]
                if main_concept:
                    expanded_queries = set([main_concept['label']] + main_concept.get('synonyms', []) + main_concept.get('related', []))
                    expanded_queries = [q for q in expanded_queries if q]
                else:
                    # Coba cari konsep dari setiap kata di query
                    for word in query_text.split():
                        c = ontology_service.find_concept(word)
                        if c:
                            expanded_queries += [c['label']] + c.get('synonyms', []) + c.get('related', [])
                    expanded_queries = list(set(expanded_queries))
                # Lakukan pencarian untuk semua query ekspansi
                all_results = []
                for q in expanded_queries:
                    res = search_service.semantic_search(
                        query=q,
                        model_type=model,
                        limit=result_limit,
                        threshold=threshold,
                        user_id=None
                    )
                    for r in res['results']:
                        r['source_query'] = q
                        all_results.append(r)
                # Gabungkan hasil berdasarkan verse_id, boost skor jika hasil dari ekspansi ontologi
                result_map = {}
                for r in all_results:
                    ref = extract_verse_ref(r)
                    if not ref:
                        continue
                    if ref not in result_map:
                        result_map[ref] = r
                    else:
                        # Boost skor jika hasil dari ekspansi ontologi
                        if r['source_query'] != query_text:
                            result_map[ref]['score'] = max(result_map[ref]['score'], r['score'] * 1.1)
                # Ambil hasil terbaik
                sorted_results = sorted(result_map.values(), key=lambda x: x['score'], reverse=True)
                found = set([extract_verse_ref(r) for r in sorted_results[:result_limit]])
                exec_time = round(time.time() - start, 3)
                label = f'Ontologi ({model})'
                result = format_eval_result(ont_key, label, found, ground_truth, exec_time)
                # Simpan ke database
                add_evaluation_result(query_id, ont_key, result['precision'], result['recall'], result['f1'], exec_time)
                results.append(result)
            except Exception as e:
                label = f'Ontologi ({model})'
                results.append({'method': ont_key, 'label': label, 'error': str(e)})

    return jsonify({'success': True, 'results': results}) 