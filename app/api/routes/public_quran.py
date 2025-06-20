"""
Public Quran-related routes for the API.
"""
from flask import Blueprint
from backend.db import get_db_connection
from ..utils import create_response, error_response

public_quran_bp = Blueprint('public_quran', __name__)

@public_quran_bp.route('/tree', methods=['GET'])
def get_public_tree():
    """
    Public API endpoint for getting the full Quran index tree.
    No authentication required.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        def get_children(parent_id=None, level=0):
            cursor.execute('''
                SELECT id, title, level, 
                       (SELECT COUNT(*) FROM quran_index qi2 WHERE qi2.parent_id = qi1.id) as child_count 
                FROM quran_index qi1
                WHERE parent_id {} ?
                ORDER BY title
            '''.format('IS' if parent_id is None else '='), (parent_id,))
            
            items = cursor.fetchall()
            result = []
            
            for item in items:
                item_dict = dict(item)
                item_dict['has_children'] = item_dict['child_count'] > 0
                if item_dict['has_children']:
                    item_dict['children'] = get_children(item['id'], level + 1)
                result.append(item_dict)
            
            return result
        
        tree = get_children()
        conn.close()
        
        return create_response(
            data=tree,
            message='Struktur indeks berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, str(e)) 