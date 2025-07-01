from flask import Blueprint, request, jsonify, session
from app.api.services.ontology_service import OntologyService
from app.api.services.search_service import SearchService
from app.auth.decorators import admin_required_api
from backend.db import get_user_by_id

ontology_bp = Blueprint('ontology', __name__)
# Gunakan database sebagai default storage
ontology_service = OntologyService(storage_type='database')
search_service = SearchService()

def is_admin():
    return session.get('user') and session['user'].get('role') == 'admin'

def get_user_info():
    """Get current user info for audit trail"""
    user_info = {}
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user:
            user_info = {
                'user_id': str(user['id']),
                'username': user['username'],
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
    return user_info

@ontology_bp.route('/admin/all', methods=['GET'])
@admin_required_api
def admin_get_all_concepts():
    """Get all concepts"""
    try:
        concepts = ontology_service.get_all()
        return jsonify({'success': True, 'concepts': concepts})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/admin/add', methods=['POST'])
@admin_required_api
def admin_add_concept():
    data = request.get_json()
    user_info = get_user_info()
    try:
        ontology_service.add_concept(data, user_info)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@ontology_bp.route('/admin/update/<concept_id>', methods=['PUT'])
@admin_required_api
def admin_update_concept(concept_id):
    data = request.get_json()
    user_info = get_user_info()
    try:
        ontology_service.update_concept(concept_id, data, user_info)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@ontology_bp.route('/admin/delete/<concept_id>', methods=['DELETE'])
@admin_required_api
def admin_delete_concept(concept_id):
    user_info = get_user_info()
    try:
        ontology_service.delete_concept(concept_id, user_info)
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

# Endpoint untuk audit trail
@ontology_bp.route('/admin/audit/log', methods=['GET'])
@admin_required_api
def admin_get_audit_log():
    """Get audit log entries"""
    try:
        concept_id = request.args.get('concept_id')
        action = request.args.get('action')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        audit_logs = ontology_service.get_audit_log(
            concept_id=concept_id,
            action=action,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True, 
            'audit_logs': audit_logs,
            'total': len(audit_logs)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/admin/audit/stats', methods=['GET'])
@admin_required_api
def admin_get_audit_stats():
    """Get audit statistics"""
    try:
        stats = ontology_service.get_audit_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/admin/audit/concept/<concept_id>', methods=['GET'])
@admin_required_api
def admin_get_concept_audit(concept_id):
    """Get audit log for specific concept"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        audit_logs = ontology_service.get_audit_log(
            concept_id=concept_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True, 
            'audit_logs': audit_logs,
            'concept_id': concept_id,
            'total': len(audit_logs)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Public endpoints
@ontology_bp.route('/search', methods=['POST'])
def search_concepts():
    """Search concepts by keyword"""
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'Query tidak boleh kosong'}), 400
    
    try:
        # Find exact match first
        concept = ontology_service.find_concept(query)
        if concept:
            return jsonify({'success': True, 'concept': concept})
        
        # If no exact match, return empty
        return jsonify({'success': True, 'concept': None})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/related/<concept_id>', methods=['GET'])
def get_related_concepts(concept_id):
    """Get related concepts"""
    try:
        related = ontology_service.get_related(concept_id)
        if related:
            return jsonify({'success': True, 'related': related})
        else:
            return jsonify({'success': False, 'message': 'Konsep tidak ditemukan'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@ontology_bp.route('/verses/<concept_id>', methods=['GET'])
def get_concept_verses(concept_id):
    """Get verses for a concept"""
    try:
        verses = ontology_service.get_verses(concept_id)
        return jsonify({'success': True, 'verses': verses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500 