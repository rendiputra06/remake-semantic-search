from flask import Blueprint, request, jsonify
from backend.db import (
    add_query, get_all_queries,
    add_relevant_verse, get_relevant_verses_by_query,
    add_evaluation_result, get_evaluation_results_by_query, get_evaluation_logs_by_query, add_evaluation_log
)
import time
import random

query_bp = Blueprint('query', __name__)

@query_bp.route('', methods=['GET'])
def list_queries():
    """Ambil semua query evaluasi"""
    data = get_all_queries()
    return jsonify({"success": True, "data": data})

@query_bp.route('', methods=['POST'])
def create_query():
    """Tambah query evaluasi baru"""
    req = request.json
    if not req or 'text' not in req:
        return jsonify({"success": False, "message": "Field 'text' wajib diisi"}), 400
    ok, result = add_query(req['text'])
    if ok:
        return jsonify({"success": True, "query_id": result})
    return jsonify({"success": False, "message": result}), 500

@query_bp.route('/<int:query_id>', methods=['GET'])
def get_query(query_id):
    """Ambil detail query dan ayat relevan"""
    from backend.db import get_all_queries
    queries = [q for q in get_all_queries() if q['id'] == query_id]
    if not queries:
        return jsonify({"success": False, "message": "Query tidak ditemukan"}), 404
    ayat = get_relevant_verses_by_query(query_id)
    return jsonify({"success": True, "data": {"query": queries[0], "relevant_verses": ayat}})

@query_bp.route('/<int:query_id>', methods=['PUT'])
def update_query(query_id):
    """Update text query evaluasi"""
    from backend.db import get_all_queries, add_query
    req = request.json
    if not req or 'text' not in req:
        return jsonify({"success": False, "message": "Field 'text' wajib diisi"}), 400
    # Sederhana: hapus lalu tambah baru (atau bisa buat update_query di db.py jika perlu)
    # Untuk sekarang, tidak implement update_query di db.py
    return jsonify({"success": False, "message": "Update query belum diimplementasi"}), 501

@query_bp.route('/<int:query_id>', methods=['DELETE'])
def delete_query(query_id):
    """Hapus query evaluasi (dan ayat relevan terkait)"""
    from backend.db import get_all_queries, get_relevant_verses_by_query, get_db_connection
    queries = [q for q in get_all_queries() if q['id'] == query_id]
    if not queries:
        return jsonify({"success": False, "message": "Query tidak ditemukan"}), 404
    # Hapus ayat relevan dan query
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM relevant_verses WHERE query_id = ?', (query_id,))
        cursor.execute('DELETE FROM queries WHERE id = ?', (query_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Query dan ayat relevan dihapus"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@query_bp.route('/<int:query_id>/relevant_verses', methods=['GET'])
def list_relevant_verses(query_id):
    """Ambil semua ayat relevan untuk query tertentu"""
    data = get_relevant_verses_by_query(query_id)
    return jsonify({"success": True, "data": data})

@query_bp.route('/<int:query_id>/relevant_verses', methods=['POST'])
def add_relevant_verse_endpoint(query_id):
    """Tambah ayat relevan ke query tertentu"""
    req = request.json
    if not req or 'verse_ref' not in req:
        return jsonify({"success": False, "message": "Field 'verse_ref' wajib diisi"}), 400
    ok, result = add_relevant_verse(query_id, req['verse_ref'])
    if ok:
        return jsonify({"success": True, "relevant_verse_id": result})
    return jsonify({"success": False, "message": result}), 500

@query_bp.route('/relevant_verse/<int:rel_id>', methods=['DELETE'])
def delete_relevant_verse(rel_id):
    """Hapus ayat relevan berdasarkan id"""
    from backend.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM relevant_verses WHERE id = ?', (rel_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ayat relevan dihapus"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@query_bp.route('/<int:query_id>/evaluate', methods=['POST'])
def evaluate_query(query_id):
    """
    Trigger evaluasi pencarian pada semua model untuk query tertentu.
    Hasil disimpan ke evaluation_results dan dikembalikan ke frontend.
    Jika skor F1 berubah, simpan ke evaluation_log.
    """
    # Ambil query dan ayat relevan
    queries = [q for q in get_all_queries() if q['id'] == query_id]
    if not queries:
        return jsonify({"success": False, "message": "Query tidak ditemukan"}), 404
    ayat = get_relevant_verses_by_query(query_id)
    if not ayat:
        return jsonify({"success": False, "message": "Ayat relevan belum diinput"}), 400
    # Dummy: list model
    models = ['word2vec', 'fasttext', 'glove', 'ontologi']
    results = []
    prev_results = {r['model']: r for r in get_evaluation_results_by_query(query_id)}
    for model in models:
        start = time.time()
        # Dummy evaluasi: precision, recall, f1 random
        precision = round(random.uniform(0.6, 1.0), 2)
        recall = round(random.uniform(0.6, 1.0), 2)
        f1 = round(2 * precision * recall / (precision + recall + 1e-8), 2)
        exec_time = round(time.time() - start, 3)
        # Simpan ke DB
        add_evaluation_result(query_id, model, precision, recall, f1, exec_time)
        # Cek perubahan F1
        prev_f1 = prev_results.get(model, {}).get('f1')
        if prev_f1 is not None and abs(prev_f1 - f1) > 1e-6:
            add_evaluation_log(query_id, model, prev_f1, f1)
        elif prev_f1 is None:
            add_evaluation_log(query_id, model, None, f1)
        results.append({
            'model': model,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'exec_time': exec_time
        })
    return jsonify({"success": True, "results": results})

@query_bp.route('/<int:query_id>/evaluation_results', methods=['GET'])
def get_evaluation_results(query_id):
    """
    Ambil hasil evaluasi terakhir per model untuk query tertentu dari tabel evaluation_results.
    """
    results = get_evaluation_results_by_query(query_id)
    if not results:
        return jsonify({"success": True, "results": []})
    # Ambil hanya hasil terbaru per model (jika ada duplikat)
    latest = {}
    for r in sorted(results, key=lambda x: x['evaluated_at'], reverse=True):
        if r['model'] not in latest:
            latest[r['model']] = r
    return jsonify({"success": True, "results": list(latest.values())})

@query_bp.route('/<int:query_id>/evaluation_logs', methods=['GET'])
def get_evaluation_logs(query_id):
    """
    Ambil log perubahan evaluasi untuk query tertentu dari tabel evaluation_log.
    """
    logs = get_evaluation_logs_by_query(query_id)
    if not logs:
        return jsonify({"success": True, "logs": []})
    # Urutkan dari terbaru ke terlama
    logs = sorted(logs, key=lambda x: x['changed_at'], reverse=True)
    return jsonify({"success": True, "logs": logs}) 