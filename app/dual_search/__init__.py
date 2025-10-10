from flask import Blueprint, render_template, request, jsonify
from typing import Dict, Any, List

from app.api.utils.model_utils import init_model
from backend.ensemble_embedding import EnsembleEmbeddingModel

blueprint = Blueprint('dual_search', __name__)

@blueprint.route('/', methods=['GET'])
def index():
    return render_template('dual_search.html')


def _merge_two_model_results(results_a: Dict[str, Dict[str, Any]],
                             results_b: Dict[str, Dict[str, Any]],
                             limit: int = 10,
                             threshold: float = None,
                             voting_bonus: float = 0.05,
                             require_both: bool = True) -> List[Dict[str, Any]]:
    # Gabungkan verse_id
    ids = set(results_a.keys()) | set(results_b.keys())
    merged = []
    sim_list = []
    for vid in ids:
        a = results_a.get(vid)
        b = results_b.get(vid)
        if require_both and (a is None or b is None):
            continue
        base = a or b
        a_sim = (a or {}).get('similarity', 0.0)
        b_sim = (b or {}).get('similarity', 0.0)
        # rata-rata sederhana + voting bonus jika keduanya muncul
        model_count = int(a is not None) + int(b is not None)
        sim = (a_sim + b_sim) / max(model_count, 1)
        if model_count >= 2:
            sim += voting_bonus
        item = {
            'verse_id': vid,
            'surah_number': base['surah_number'],
            'surah_name': base['surah_name'],
            'ayat_number': base['ayat_number'],
            'arabic': base['arabic'],
            'translation': base['translation'],
            'similarity': sim,
            'individual_scores': {
                'model_a': a_sim,
                'model_b': b_sim,
            },
            'model_count': model_count,
        }
        merged.append(item)
        sim_list.append(sim)
    # Threshold adaptif jika threshold None
    if threshold is None and sim_list:
        import numpy as np
        perc = np.percentile(sim_list, 75)
        threshold = 0.5 if (np.isnan(perc) or perc == 0) else float(perc)
    if threshold is not None:
        merged = [r for r in merged if r['similarity'] >= threshold]
    merged.sort(key=lambda x: x['similarity'], reverse=True)
    return merged[:limit] if limit is not None else merged


def _summarize_results(results: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
    """Return summary with total hits and top-K verse refs like Qs.X:Y."""
    total = len(results)
    top_items = results[:top_k] if top_k is not None else results
    def fmt(item):
        return f"Qs.{item.get('surah_number')}:{item.get('ayat_number')}"
    return {
        'total': total,
        'top_refs': [fmt(it) for it in top_items]
    }


@blueprint.route('/search', methods=['POST'])
def search():
    data = request.form if request.form else request.json
    query = (data.get('query') or '').strip()
    combo = (data.get('combo') or 'w2v_ft').strip()
    limit = data.get('limit')
    try:
        limit = int(limit) if limit is not None else 10
    except Exception:
        limit = 10
    threshold = data.get('threshold')
    try:
        threshold = float(threshold) if threshold not in (None, '', 'null') else None
    except Exception:
        threshold = None

    if not query:
        return render_template('dual_search.html', error='Query tidak boleh kosong', query=query, combo=combo)

    # Inisialisasi model sesuai kebutuhan
    w2v = ft = gv = None
    results: List[Dict[str, Any]] = []
    model_summaries: Dict[str, Dict[str, Any]] = {}

    if combo == 'ensemble3':
        # Gunakan ensemble 3 model yang sudah tersedia
        w2v = init_model('word2vec')
        ft = init_model('fasttext')
        gv = init_model('glove')
        # Kumpulkan hasil per-model untuk summary (limit=None untuk total sebenarnya)
        w2v_list = w2v.search(query, limit=None, threshold=threshold)
        ft_list = ft.search(query, limit=None, threshold=threshold)
        gv_list = gv.search(query, limit=None, threshold=threshold)
        model_summaries['word2vec'] = _summarize_results(w2v_list, top_k=limit)
        model_summaries['fasttext'] = _summarize_results(ft_list, top_k=limit)
        model_summaries['glove'] = _summarize_results(gv_list, top_k=limit)

        ensemble = EnsembleEmbeddingModel(w2v, ft, gv, use_meta_ensemble=False, use_voting_filter=True)
        # ensemble.search akan memanggil search setiap model di dalamnya
        results = ensemble.search(query, limit=limit, threshold=threshold)
    else:
        # Ambil semua hasil per model untuk menghitung total, lalu merge dan batasi top-N
        # Menggunakan limit=None agar total mencerminkan jumlah sebenarnya setelah threshold
        base_limit = None
        if combo == 'w2v_ft':
            w2v = init_model('word2vec')
            ft = init_model('fasttext')
            w2v_list = w2v.search(query, limit=base_limit, threshold=threshold)
            ft_list = ft.search(query, limit=base_limit, threshold=threshold)
            model_summaries['word2vec'] = _summarize_results(w2v_list, top_k=limit)
            model_summaries['fasttext'] = _summarize_results(ft_list, top_k=limit)
            a = {r['verse_id']: r for r in w2v_list}
            b = {r['verse_id']: r for r in ft_list}
            results = _merge_two_model_results(a, b, limit=limit, threshold=threshold)
        elif combo == 'w2v_glove':
            w2v = init_model('word2vec')
            gv = init_model('glove')
            w2v_list = w2v.search(query, limit=base_limit, threshold=threshold)
            gv_list = gv.search(query, limit=base_limit, threshold=threshold)
            model_summaries['word2vec'] = _summarize_results(w2v_list, top_k=limit)
            model_summaries['glove'] = _summarize_results(gv_list, top_k=limit)
            a = {r['verse_id']: r for r in w2v_list}
            b = {r['verse_id']: r for r in gv_list}
            results = _merge_two_model_results(a, b, limit=limit, threshold=threshold)
        elif combo == 'ft_glove':
            ft = init_model('fasttext')
            gv = init_model('glove')
            ft_list = ft.search(query, limit=base_limit, threshold=threshold)
            gv_list = gv.search(query, limit=base_limit, threshold=threshold)
            model_summaries['fasttext'] = _summarize_results(ft_list, top_k=limit)
            model_summaries['glove'] = _summarize_results(gv_list, top_k=limit)
            a = {r['verse_id']: r for r in ft_list}
            b = {r['verse_id']: r for r in gv_list}
            results = _merge_two_model_results(a, b, limit=limit, threshold=threshold)
        else:
            return render_template('dual_search.html', error='Pilihan kombinasi tidak valid', query=query, combo=combo)

    return render_template('dual_search.html', query=query, combo=combo, results=results, model_summaries=model_summaries)
