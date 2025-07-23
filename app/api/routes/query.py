from flask import Blueprint, request, jsonify
from backend.db import (
    add_query, get_all_queries, delete_query as db_delete_query,
    add_relevant_verse, add_relevant_verses_batch, get_relevant_verses_by_query, delete_relevant_verse as db_delete_relevant_verse,
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

@query_bp.route('/<int:query_id>', methods=['DELETE'])
def delete_query(query_id):
    """Hapus query evaluasi"""
    ok, message = db_delete_query(query_id)
    if ok:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "message": message}), 500

@query_bp.route('/<int:query_id>/relevant_verses', methods=['GET'])
def get_relevant_verses(query_id):
    """Ambil ayat relevan untuk query tertentu"""
    verses = get_relevant_verses_by_query(query_id)
    return jsonify({"success": True, "data": verses})

@query_bp.route('/<int:query_id>/relevant_verses', methods=['POST'])
def add_relevant_verse_to_query(query_id):
    """Tambah ayat relevan untuk query tertentu"""
    req = request.json
    if not req or 'verse_ref' not in req:
        return jsonify({"success": False, "message": "Field 'verse_ref' wajib diisi"}), 400
    
    ok, result = add_relevant_verse(query_id, req['verse_ref'])
    if ok:
        return jsonify({"success": True, "verse_id": result})
    return jsonify({"success": False, "message": result}), 500

@query_bp.route('/relevant_verse/<int:verse_id>', methods=['DELETE'])
def delete_relevant_verse(verse_id):
    """Hapus ayat relevan berdasarkan ID"""
    ok, message = db_delete_relevant_verse(verse_id)
    if ok:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "message": message}), 500

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

@query_bp.route('/import-ayat-excel', methods=['POST'])
# @admin_required
def import_ayat_excel():
    """
    Import ayat relevan dari data Excel (frontend kirim list ayat).
    Format request: { ayat: ["2:255", "1:1", ...], query_id: <id> }
    """
    try:
        data = request.get_json()
        ayat_list = data.get('ayat', [])
        query_id = data.get('query_id')
        if not ayat_list or not isinstance(ayat_list, list):
            return jsonify({'success': False, 'message': 'Data ayat tidak valid.'}), 400
        if not query_id:
            return jsonify({'success': False, 'message': 'Query ID wajib dipilih.'}), 400
        # Gunakan batch insert agar lebih cepat
        success, result = add_relevant_verses_batch(query_id, ayat_list)
        if success:
            return jsonify({'success': True, 'message': f'{result} ayat berhasil diimport.'})
        else:
            return jsonify({'success': False, 'message': result}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500