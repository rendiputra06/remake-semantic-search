from flask import Blueprint, request, jsonify, session
from app.api.services.ontology_service import OntologyService
from app.api.services.search_service import SearchService
from app.auth.decorators import admin_required_api

ontology_bp = Blueprint('ontology', __name__)
# Gunakan database sebagai default storage
ontology_service = OntologyService(storage_type='database')
search_service = SearchService()

def is_admin():
    return session.get('user') and session['user'].get('role') == 'admin'

@ontology_bp.route('/admin/all', methods=['GET'])
@admin_required_api
def admin_get_all():
    return jsonify({'success': True, 'concepts': ontology_service.get_all()})

@ontology_bp.route('/admin/add', methods=['POST'])
@admin_required_api
def admin_add_concept():
    data = request.get_json()
    try:
        ontology_service.add_concept(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@ontology_bp.route('/admin/update/<concept_id>', methods=['PUT'])
@admin_required_api
def admin_update_concept(concept_id):
    data = request.get_json()
    try:
        ontology_service.update_concept(concept_id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@ontology_bp.route('/admin/delete/<concept_id>', methods=['DELETE'])
@admin_required_api
def admin_delete_concept(concept_id):
    try:
        ontology_service.delete_concept(concept_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@ontology_bp.route('/related', methods=['GET'])
def get_related():
    """
    Endpoint untuk mendapatkan konsep dan relasi terkait dari ontologi.
    Query param: keyword (id/label/sinonim)
    """
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': 'Parameter keyword wajib diisi'}), 400
    concept = ontology_service.find_concept(keyword)
    if not concept:
        return jsonify({'success': False, 'message': 'Konsep tidak ditemukan'}), 404
    related = ontology_service.get_related(concept['id'])
    return jsonify({
        'success': True,
        'concept': concept,
        'related': related
    })

@ontology_bp.route('/search', methods=['POST'])
def ontology_search():
    """
    Endpoint pencarian semantik dengan ekspansi ontologi.
    Body: {"query": ..., "model": ..., "limit": ..., "threshold": ...}
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak diberikan'}), 400
    query = data.get('query', '').strip()
    model_type = data.get('model', 'word2vec')
    limit = int(data.get('limit', 10))
    threshold = float(data.get('threshold', 0.5))
    if not query:
        return jsonify({'success': False, 'message': 'Query tidak boleh kosong'}), 400

    # Ekspansi query dengan ontologi
    main_concept = ontology_service.find_concept(query)
    expanded_queries = [query]
    expanded_info = []
    if main_concept:
        # Tambahkan label, sinonim, dan related
        expanded_queries = set([main_concept['label']] + main_concept.get('synonyms', []) + main_concept.get('related', []))
        expanded_queries = [q for q in expanded_queries if q]
        expanded_info = expanded_queries.copy()
    else:
        # Coba cari konsep dari setiap kata di query
        for word in query.split():
            c = ontology_service.find_concept(word)
            if c:
                expanded_queries += [c['label']] + c.get('synonyms', []) + c.get('related', [])
        expanded_queries = list(set(expanded_queries))
        expanded_info = expanded_queries.copy()

    # Lakukan pencarian untuk semua query ekspansi
    all_results = []
    for q in expanded_queries:
        results = search_service.semantic_search(q, model_type=model_type, limit=limit, threshold=threshold)
        for r in results['results']:
            r['source_query'] = q
            all_results.append(r)

    # Gabungkan hasil berdasarkan verse_id, boost skor jika hasil dari ekspansi ontologi
    result_map = {}
    for r in all_results:
        vid = r['verse_id']
        if vid not in result_map or r['similarity'] > result_map[vid]['similarity']:
            result_map[vid] = r
        # Boost skor jika source_query adalah sinonim/related
        if r['source_query'] != query:
            result_map[vid]['similarity'] = min(result_map[vid]['similarity'] + 0.1, 1.0)
            result_map[vid]['boosted'] = True
        else:
            result_map[vid]['boosted'] = False

    # Urutkan hasil
    final_results = list(result_map.values())
    final_results.sort(key=lambda x: x['similarity'], reverse=True)
    final_results = final_results[:limit]

    return jsonify({
        'success': True,
        'query': query,
        'expanded_queries': expanded_info,
        'results': final_results,
        'count': len(final_results)
    })

# Endpoint untuk manajemen storage (admin only)
@ontology_bp.route('/admin/storage/info', methods=['GET'])
@admin_required_api
def admin_storage_info():
    """Get storage information"""
    info = ontology_service.get_storage_info()
    return jsonify({'success': True, 'info': info})

@ontology_bp.route('/admin/storage/switch', methods=['POST'])
@admin_required_api
def admin_switch_storage():
    """Switch storage type"""
    data = request.get_json()
    storage_type = data.get('storage_type', 'database')
    
    if storage_type not in ['json', 'database']:
        return jsonify({'success': False, 'message': 'Storage type harus json atau database'}), 400
    
    try:
        success = ontology_service.switch_storage(storage_type)
        if success:
            return jsonify({
                'success': True, 
                'message': f'Berhasil switch ke {storage_type} storage',
                'storage_type': storage_type
            })
        else:
            return jsonify({'success': False, 'message': 'Gagal switch storage'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/admin/storage/sync', methods=['POST'])
@admin_required_api
def admin_sync_storage():
    """Sync data between storage types"""
    data = request.get_json()
    direction = data.get('direction', 'json_to_db')  # json_to_db or db_to_json
    
    try:
        if direction == 'json_to_db':
            success = ontology_service.sync_to_database()
            message = 'Berhasil sync JSON ke database'
        elif direction == 'db_to_json':
            success = ontology_service.export_to_json()
            message = 'Berhasil export database ke JSON'
        else:
            return jsonify({'success': False, 'message': 'Direction harus json_to_db atau db_to_json'}), 400
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Gagal sync data'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500 