from flask import Blueprint, jsonify, request
from backend.db import (
    get_db_connection, 
    get_quran_indexes,
    get_quran_index_by_id,
    get_quran_ayat_by_index,
    add_quran_index,
    update_quran_index
)

quran_index_bp = Blueprint('quran_index', __name__)

@quran_index_bp.route('/tree', methods=['GET'])
def get_index_tree():
    """
    Mendapatkan seluruh index Al-Quran dalam format tree
    """
    def build_tree(parent_id=None):
        indexes = get_quran_indexes(parent_id)
        
        for index in indexes:
            index_id = index['id']
            
            # Check if has ayat
            ayat = get_quran_ayat_by_index(index_id)
            index['has_ayat'] = len(ayat) > 0
            index['ayat_count'] = len(ayat)
            
            # Get children recursively
            children = build_tree(index_id)
            if children:
                index['children'] = children
                index['has_children'] = True
            else:
                index['children'] = []
                index['has_children'] = False
        
        return indexes

    try:
        tree = build_tree()
        return jsonify({
            'success': True,
            'data': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat membangun tree: {str(e)}'
        }), 500

@quran_index_bp.route('/all', methods=['GET'])
def get_all_indexes():
    """
    Mendapatkan seluruh daftar index untuk keperluan dropdown, dll
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, parent_id, level FROM quran_index ORDER BY level, title')
    all_indexes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': all_indexes
    })

@quran_index_bp.route('/roots', methods=['GET'])
def get_root_indexes():
    """
    Mendapatkan daftar indeks utama/root Al-Quran (tanpa parent)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, title, level 
    FROM quran_index 
    WHERE parent_id IS NULL 
    ORDER BY title
    ''')
    
    root_indexes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'data': root_indexes
    })

@quran_index_bp.route('/', methods=['GET'])
def get_indexes():
    """
    Mendapatkan daftar index Al-Quran
    Query param:
    - parent_id: ID parent index (opsional)
    """
    parent_id = request.args.get('parent_id')
    
    # Konversi parent_id ke integer jika ada
    if parent_id:
        try:
            parent_id = int(parent_id)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Parameter parent_id harus berupa angka'
            }), 400
    
    indexes = get_quran_indexes(parent_id)
    
    # Tandai apakah index memiliki sub-index atau ayat
    for index in indexes:
        sub_indexes = get_quran_indexes(index['id'])
        ayat = get_quran_ayat_by_index(index['id'])
        
        index['has_children'] = len(sub_indexes) > 0
        index['has_ayat'] = len(ayat) > 0
        index['ayat_count'] = len(ayat)
    
    return jsonify({
        'success': True,
        'data': indexes
    })

@quran_index_bp.route('/<int:index_id>', methods=['GET'])
def get_index_by_id(index_id):
    """
    Mendapatkan detail index Al-Quran berdasarkan ID
    """
    index = get_quran_index_by_id(index_id)
    
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    # Dapatkan sub-index dan ayat
    sub_indexes = get_quran_indexes(index_id)
    ayat = get_quran_ayat_by_index(index_id)
    
    # Dapatkan parent jika ada
    parent = None
    if index['parent_id']:
        parent = get_quran_index_by_id(index['parent_id'])
    
    return jsonify({
        'success': True,
        'data': {
            'index': index,
            'parent': parent,
            'sub_indexes': sub_indexes,
            'ayat': ayat
        }
    })

@quran_index_bp.route('/', methods=['POST'])
def add_index():
    """
    Menambahkan index Al-Quran baru
    """
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Data title harus disertakan'
        }), 400
    
    # Tentukan level berdasarkan parent
    level = 1
    parent_id = data.get('parent_id')
    if parent_id:
        parent = get_quran_index_by_id(parent_id)
        if not parent:
            return jsonify({
                'success': False,
                'message': 'Parent index tidak ditemukan'
            }), 404
        level = parent['level'] + 1
    
    success, result = add_quran_index(
        title=data['title'],
        description=data.get('description'),
        parent_id=parent_id,
        level=level,
        sort_order=data.get('sort_order', 0)
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Index berhasil ditambahkan',
            'data': {
                'id': result
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Gagal menambahkan index: {result}'
        }), 500

@quran_index_bp.route('/<int:index_id>', methods=['PUT'])
def update_index(index_id):
    """
    Memperbarui index Al-Quran
    """
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Data title harus disertakan'
        }), 400
    
    # Cek apakah index ada
    index = get_quran_index_by_id(index_id)
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    # Tentukan level berdasarkan parent
    level = 1
    parent_id = data.get('parent_id')
    if parent_id:
        parent = get_quran_index_by_id(parent_id)
        if not parent:
            return jsonify({
                'success': False,
                'message': 'Parent index tidak ditemukan'
            }), 404
        level = parent['level'] + 1
    
    success, message = update_quran_index(
        index_id=index_id,
        title=data['title'],
        description=data.get('description'),
        parent_id=parent_id,
        level=level,
        sort_order=data.get('sort_order', 0)
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500

@quran_index_bp.route('/<int:index_id>', methods=['DELETE'])
def delete_index(index_id):
    """
    Menghapus index Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cek apakah index memiliki child
    cursor.execute('SELECT COUNT(*) as count FROM quran_index WHERE parent_id = ?', (index_id,))
    child_count = cursor.fetchone()['count']
    
    if child_count > 0:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Index tidak dapat dihapus karena memiliki sub-index'
        }), 400
    
    try:
        cursor.execute('DELETE FROM quran_index WHERE id = ?', (index_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Index berhasil dihapus'
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Gagal menghapus index: {str(e)}'
        }), 500
