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
    limit_raw = data.get('limit')
    threshold_raw = data.get('threshold')
    
    if not query:
        return jsonify({'success': False, 'message': 'Query tidak boleh kosong'}), 400

    # Jika limit atau threshold tidak diberikan, gunakan pengaturan dari database
    limit = None
    threshold = None
    
    if limit_raw is not None:
        limit = int(limit_raw) if limit_raw != 0 else None
    if threshold_raw is not None:
        threshold = float(threshold_raw)

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
        results = search_service.semantic_search(q, model_type=model_type, limit=limit, threshold=threshold, user_id=session.get('user_id'))
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

@ontology_bp.route('/trace', methods=['POST'])
def ontology_trace():
    """
    Endpoint tracing proses pencarian semantik & ontologi.
    Body: {"query": ..., "model": ..., "limit": ..., "threshold": ...}
    Response: data intermediate (trace/log) di setiap langkah.
    """
    import time
    start_time = time.time()
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak diberikan'}), 400
    query = data.get('query', '').strip()
    model_type = data.get('model', 'word2vec')
    limit = int(data.get('limit', 10))
    threshold = float(data.get('threshold', 0.5))
    if not query:
        return jsonify({'success': False, 'message': 'Query tidak boleh kosong'}), 400

    trace = {
        'query': query,
        'model': model_type,
        'limit': limit,
        'threshold': threshold,
        'steps': [],
        'logs': [],
        'metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr
        }
    }

    try:
        # Step 1: Ekspansi Ontologi
        step_start = time.time()
        main_concept = ontology_service.find_concept(query)
        expanded_queries = [query]
        expanded_info = []
        ontology_data = []
        
        if main_concept:
            expanded_queries = set([main_concept['label']] + main_concept.get('synonyms', []) + main_concept.get('related', []))
            expanded_queries = [q for q in expanded_queries if q]
            expanded_info = expanded_queries.copy()
            ontology_data.append(main_concept)
            # Ambil data konsep hasil ekspansi
            for q in expanded_queries:
                c = ontology_service.find_concept(q)
                if c and c not in ontology_data:
                    ontology_data.append(c)
        else:
            for word in query.split():
                c = ontology_service.find_concept(word)
                if c:
                    expanded_queries += [c['label']] + c.get('synonyms', []) + c.get('related', [])
            expanded_queries = list(set(expanded_queries))
            expanded_info = expanded_queries.copy()
            for q in expanded_queries:
                c = ontology_service.find_concept(q)
                if c and c not in ontology_data:
                    ontology_data.append(c)

        step_duration = (time.time() - step_start) * 1000
        trace['steps'].append({
            'step': 'ontology_expansion', 
            'data': {
                'main_concept': main_concept,
                'expanded_queries': expanded_queries,
                'ontology_data': ontology_data,
                'duration_ms': round(step_duration, 2)
            },
            'logs': [f'Ekspansi ontologi selesai dalam {step_duration:.2f}ms']
        })
        trace['logs'].append(f'Ekspansi ontologi: {expanded_queries}')

        # Step 2: Pencarian Semantik untuk setiap ekspansi
        step_start = time.time()
        all_results = []
        semantic_traces = []
        
        for q in expanded_queries:
            sub_trace = {'query': q, 'steps': [], 'logs': []}
            sub_start = time.time()
            results = search_service.semantic_search(q, model_type=model_type, limit=limit, threshold=threshold, trace=sub_trace)
            sub_duration = (time.time() - sub_start) * 1000
            sub_trace['duration_ms'] = round(sub_duration, 2)
            sub_trace['result_count'] = len(results['results'])
            
            for r in results['results']:
                r['source_query'] = q
                all_results.append(r)
            semantic_traces.append(sub_trace)
        
        step_duration = (time.time() - step_start) * 1000
        trace['steps'].append({
            'step': 'semantic_search', 
            'data': semantic_traces,
            'duration_ms': round(step_duration, 2),
            'logs': [f'Selesai pencarian semantik untuk {len(expanded_queries)} query dalam {step_duration:.2f}ms']
        })
        trace['logs'].append(f'Selesai pencarian semantik untuk semua ekspansi, total hasil: {len(all_results)}')

        # Step 3: Boosting & Ranking
        step_start = time.time()
        result_map = {}
        boosting_log = []
        boosted_count = 0
        
        for r in all_results:
            vid = r['verse_id']
            if vid not in result_map or r['similarity'] > result_map[vid]['similarity']:
                result_map[vid] = r
            if r['source_query'] != query:
                before = result_map[vid]['similarity']
                result_map[vid]['similarity'] = min(result_map[vid]['similarity'] + 0.1, 1.0)
                result_map[vid]['boosted'] = True
                boosted_count += 1
                boosting_log.append({
                    'verse_id': vid, 
                    'before': before, 
                    'after': result_map[vid]['similarity'], 
                    'source_query': r['source_query'],
                    'boost_amount': round((result_map[vid]['similarity'] - before) * 100, 2)
                })
            else:
                result_map[vid]['boosted'] = False
        
        final_results = list(result_map.values())
        final_results.sort(key=lambda x: x['similarity'], reverse=True)
        final_results = final_results[:limit]
        
        step_duration = (time.time() - step_start) * 1000
        trace['steps'].append({
            'step': 'boosting_ranking', 
            'data': boosting_log,
            'duration_ms': round(step_duration, 2),
            'logs': [
                f'Boosting dan ranking selesai dalam {step_duration:.2f}ms',
                f'Total ayat yang di-boost: {boosted_count}',
                f'Hasil akhir: {len(final_results)} ayat'
            ]
        })
        
        # Tambahkan statistik akhir
        total_duration = (time.time() - start_time) * 1000
        trace['final_results'] = final_results
        trace['result_count'] = len(final_results)
        trace['total_duration_ms'] = round(total_duration, 2)
        trace['statistics'] = {
            'total_queries': len(expanded_queries),
            'total_initial_results': len(all_results),
            'boosted_results': boosted_count,
            'final_results': len(final_results),
            'average_similarity': round(sum(r['similarity'] for r in final_results) / len(final_results), 4) if final_results else 0
        }
        
        trace['logs'].append(f'Proses tracing selesai dalam {total_duration:.2f}ms')
        return jsonify({'success': True, 'trace': trace})
    except Exception as e:
        total_duration = (time.time() - start_time) * 1000
        trace['logs'].append(f'Error: {str(e)}')
        trace['error'] = str(e)
        trace['total_duration_ms'] = round(total_duration, 2)
        return jsonify({'success': False, 'trace': trace, 'message': str(e)}), 500 