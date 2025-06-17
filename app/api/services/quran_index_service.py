"""
Quran index service implementation.
"""
from typing import Dict, List, Optional, Tuple
import json
from backend.db import (
    get_db_connection,
    get_quran_indexes,
    get_quran_index_by_id,
    add_quran_index,
    update_quran_index,
    update_quran_index_ayat
)

class QuranIndexService:
    """Service class for handling Quran index operations."""
    
    def get_index_tree(self) -> Dict:
        """Get Quran index in tree format."""
        try:
            indexes = get_quran_indexes()
            
            # Build tree structure
            tree = []
            index_map = {}
            
            # First pass: create nodes
            for idx in indexes:
                index_map[idx['id']] = {
                    'id': idx['id'],
                    'title': idx['title'],
                    'description': idx.get('description'),
                    'children': []
                }
            
            # Second pass: build tree
            for idx in indexes:
                node = index_map[idx['id']]
                if idx.get('parent_id') is None:
                    tree.append(node)
                else:
                    parent = index_map.get(idx['parent_id'])
                    if parent:
                        parent['children'].append(node)
            
            return {
                'success': True,
                'data': tree
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat membangun tree index: {str(e)}'
            }
    
    def get_root_indexes(self) -> Dict:
        """Get root level indexes."""
        try:
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
            
            return {
                'success': True,
                'data': root_indexes
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mengambil root index: {str(e)}'
            }
    
    def get_all_indexes(self) -> Dict:
        """Get all indexes for dropdown lists etc."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, title, parent_id, level FROM quran_index ORDER BY level, title')
            all_indexes = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'data': all_indexes
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mengambil semua index: {str(e)}'
            }
    
    def get_index_by_id(self, index_id: int) -> Dict:
        """Get index details by ID."""
        try:
            index = get_quran_index_by_id(index_id)
            if not index:
                return {
                    'success': False,
                    'message': 'Index tidak ditemukan'
                }
                
            return {
                'success': True,
                'data': index
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mengambil detail index: {str(e)}'
            }
    
    def add_index(self, title: str, description: Optional[str] = None,
                 parent_id: Optional[int] = None, sort_order: int = 0) -> Dict:
        """Add new index."""
        try:
            # Validate parent if provided
            level = 1
            if parent_id:
                parent = get_quran_index_by_id(parent_id)
                if not parent:
                    return {
                        'success': False,
                        'message': 'Parent index tidak ditemukan'
                    }
                level = parent['level'] + 1
            
            success, result = add_quran_index(
                title=title,
                description=description,
                parent_id=parent_id,
                level=level,
                sort_order=sort_order
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Index berhasil ditambahkan',
                    'data': {'id': result}
                }
            else:
                return {
                    'success': False,
                    'message': f'Gagal menambahkan index: {result}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat menambahkan index: {str(e)}'
            }
    
    def update_index(self, index_id: int, title: str,
                    description: Optional[str] = None,
                    parent_id: Optional[int] = None,
                    sort_order: Optional[int] = None) -> Dict:
        """Update existing index."""
        try:
            # Validate index exists
            index = get_quran_index_by_id(index_id)
            if not index:
                return {
                    'success': False,
                    'message': 'Index tidak ditemukan'
                }
            
            # Validate parent is not self or child
            if parent_id:
                if parent_id == index_id:
                    return {
                        'success': False,
                        'message': 'Parent tidak boleh dirinya sendiri'
                    }
                
                parent = get_quran_index_by_id(parent_id)
                if not parent:
                    return {
                        'success': False,
                        'message': 'Parent index tidak ditemukan'
                    }
                
                level = parent['level'] + 1
            else:
                level = 1
            
            success, message = update_quran_index(
                index_id=index_id,
                title=title,
                description=description,
                parent_id=parent_id,
                level=level,
                sort_order=sort_order
            )
            
            return {
                'success': success,
                'message': message
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat memperbarui index: {str(e)}'
            }
    
    def update_index_ayat(self, index_id: int, ayat_list: List[str]) -> Dict:
        """Update ayat list for an index."""
        try:
            # Validate index exists
            index = get_quran_index_by_id(index_id)
            if not index:
                return {
                    'success': False,
                    'message': 'Index tidak ditemukan'
                }
            
            success, message = update_quran_index_ayat(index_id, ayat_list)
            
            return {
                'success': success,
                'message': message
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat memperbarui daftar ayat: {str(e)}'
            }
    
    def get_index_stats(self) -> Dict:
        """Get statistics about Quran index and verses."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all indexes with ayat
            cursor.execute('SELECT id, title, level, parent_id, list_ayat FROM quran_index')
            indexes_with_ayat = cursor.fetchall()
            
            # Calculate statistics
            total_categories = len(indexes_with_ayat)
            total_ayat = 0
            categories_with_ayat = 0
            level_stats = {}
            parent_type_stats = {}
            surah_stats = {}
            
            for idx in indexes_with_ayat:
                # Count by level
                level = idx['level']
                if level in level_stats:
                    level_stats[level] += 1
                else:
                    level_stats[level] = 1
                
                # Count by parent type
                parent_type = 'root' if idx['parent_id'] is None else 'child'
                if parent_type in parent_type_stats:
                    parent_type_stats[parent_type] += 1
                else:
                    parent_type_stats[parent_type] = 1
                
                # Process ayat list
                if idx['list_ayat']:
                    try:
                        ayat_list = json.loads(idx['list_ayat'])
                        if ayat_list and len(ayat_list) > 0:
                            categories_with_ayat += 1
                            total_ayat += len(ayat_list)
                            
                            # Count by surah
                            for ayat_ref in ayat_list:
                                surah = ayat_ref.split(':')[0]
                                if surah in surah_stats:
                                    surah_stats[surah] += 1
                                else:
                                    surah_stats[surah] = 1
                    except json.JSONDecodeError:
                        continue
            
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'total_categories': total_categories,
                    'total_ayat': total_ayat,
                    'categories_with_ayat': categories_with_ayat,
                    'level_stats': level_stats,
                    'parent_type_stats': parent_type_stats,
                    'surah_stats': surah_stats
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mendapatkan statistik: {str(e)}'
            }