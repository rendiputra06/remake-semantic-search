"""
Quran index management routes for the semantic search API.
"""
from flask import Blueprint, request, session
from werkzeug.utils import secure_filename
import os
from marshmallow import ValidationError
import tempfile
import time
import json

from ..utils import create_response, error_response, validation_error_response
from app.api.schemas_main import QuranIndexImportRequest
from app.auth.decorators import admin_required_api
from backend.db import (
    get_quran_index_by_id, get_quran_indexes, get_quran_ayat_by_index,
    add_quran_index, update_quran_index, delete_quran_index,
    update_quran_index_ayat, get_user_by_id, get_db_connection
)
from backend.excel_importer import excel_to_hierarchy_db, get_excel_sheets

quran_index_bp = Blueprint('quran_index', __name__)

@quran_index_bp.route('/roots', methods=['GET'])
@admin_required_api
def get_roots():
    """API endpoint for getting root Quran indices."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, level FROM quran_index 
            WHERE parent_id IS NULL 
            ORDER BY title
        ''')
        roots = cursor.fetchall()
        conn.close()
        
        return create_response(
            data=[dict(root) for root in roots],
            message='Daftar indeks utama berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, str(e))

@quran_index_bp.route('/tree', methods=['GET'])
@admin_required_api
def get_tree():
    """API endpoint for getting the full Quran index tree."""
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

@quran_index_bp.route('/import-excel', methods=['POST'])
@admin_required_api
def import_excel():
    """API endpoint for importing Quran index from Excel."""
    try:
        if 'file' not in request.files:
            return error_response(400, 'File tidak diunggah')
        
        file = request.files['file']
        if file.filename == '':
            return error_response(400, 'Tidak ada file yang dipilih')
        
        # Validate request data
        schema = QuranIndexImportRequest()
        data = schema.load(request.form)
        
        # Save file temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)
        
        # Import Excel data
        success, message = excel_to_hierarchy_db(
            file_path,
            data['sheet_name'],
            data.get('parent_id')
        )
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if success:
            return create_response(
                message=message
            )
        else:
            return error_response(500, message)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, str(e))

@quran_index_bp.route('/<int:index_id>', methods=['GET'])
def get_index_by_id(index_id):
    """
    Endpoint untuk mendapatkan detail index Al-Quran berdasarkan ID
    """
    try:
        index = get_quran_index_by_id(index_id)
        
        if not index:
            return error_response(404, 'Index tidak ditemukan')
        
        # Dapatkan sub-index dan ayat
        sub_indexes = get_quran_indexes(index_id)
        ayat = get_quran_ayat_by_index(index_id)
        
        # Dapatkan parent jika ada
        parent = None
        if index['parent_id']:
            parent = get_quran_index_by_id(index['parent_id'])
        
        return create_response(
            data={
                'index': index,
                'parent': parent,
                'sub_indexes': sub_indexes,
                'ayat': ayat
            },
            message='Detail index berhasil diambil'
        )
    except Exception as e:
        return error_response(500, f'Error saat mendapatkan detail index: {str(e)}')

@quran_index_bp.route('', methods=['POST'])
def add_index():
    """
    Endpoint untuk menambahkan index Al-Quran baru
    Memerlukan autentikasi sebagai admin
    """
    try:
        if 'user_id' not in session:
            return error_response(401, 'Anda harus login untuk mengakses fitur ini')
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return error_response(403, 'Anda tidak memiliki akses untuk fitur ini')
        
        data = request.json
        
        if not data or 'title' not in data:
            return error_response(400, 'Data tidak lengkap, title harus diisi')
        
        # Validasi parent_id jika ada
        parent_id = data.get('parent_id')
        level = 1
        
        if parent_id:
            parent = get_quran_index_by_id(parent_id)
            if not parent:
                return error_response(404, 'Parent index tidak ditemukan')
            level = parent['level'] + 1
        
        success, result = add_quran_index(
            title=data['title'],
            description=data.get('description'),
            parent_id=parent_id,
            level=level,
            sort_order=data.get('sort_order', 0)
        )
        
        if success:
            return create_response(
                data={'id': result},
                message='Index berhasil ditambahkan'
            )
        else:
            return error_response(500, f'Gagal menambahkan index: {result}')
    except Exception as e:
        return error_response(500, f'Error saat menambahkan index: {str(e)}')

@quran_index_bp.route('/<int:index_id>', methods=['PUT'])
def update_index(index_id):
    """
    Endpoint untuk memperbarui index Al-Quran
    Memerlukan autentikasi sebagai admin
    """
    try:
        if 'user_id' not in session:
            return error_response(401, 'Anda harus login untuk mengakses fitur ini')
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return error_response(403, 'Anda tidak memiliki akses untuk fitur ini')
        
        data = request.json
        
        if not data or 'title' not in data:
            return error_response(400, 'Data tidak lengkap, title harus diisi')
        
        # Periksa apakah index ada
        index = get_quran_index_by_id(index_id)
        if not index:
            return error_response(404, 'Index tidak ditemukan')
        
        # Validasi parent_id jika ada
        parent_id = data.get('parent_id')
        level = 1
        
        if parent_id:
            # Validasi bahwa parent bukan dirinya sendiri atau anak dari index ini
            if parent_id == index_id:
                return error_response(400, 'Parent tidak boleh dirinya sendiri')
                
            # Periksa apakah parent valid
            parent = get_quran_index_by_id(parent_id)
            if not parent:
                return error_response(404, 'Parent index tidak ditemukan')
                
            # Hitung level baru
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
            return create_response(message=message)
        else:
            return error_response(500, message)
    except Exception as e:
        return error_response(500, f'Error saat memperbarui index: {str(e)}')

@quran_index_bp.route('/<int:index_id>', methods=['DELETE'])
def delete_index(index_id):
    """
    Endpoint untuk menghapus index Al-Quran
    Memerlukan autentikasi sebagai admin
    """
    try:
        if 'user_id' not in session:
            return error_response(401, 'Anda harus login untuk mengakses fitur ini')
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return error_response(403, 'Anda tidak memiliki akses untuk fitur ini')
        
        # Periksa apakah index ada
        index = get_quran_index_by_id(index_id)
        if not index:
            return error_response(404, 'Index tidak ditemukan')
        
        success, message = delete_quran_index(index_id)
        
        if success:
            return create_response(message=message)
        else:
            return error_response(500, message)
    except Exception as e:
        return error_response(500, f'Error saat menghapus index: {str(e)}')

@quran_index_bp.route('/excel/check-deps', methods=['GET'])
def check_excel_dependencies():
    """
    Endpoint untuk mengecek dependency Excel
    """
    try:
        import pandas as pd
        return create_response(
            data={'pandas_available': True, 'version': pd.__version__},
            message='Dependency Excel tersedia'
        )
    except ImportError as e:
        return error_response(500, f'Dependency tidak tersedia: {str(e)}')
    except Exception as e:
        return error_response(500, f'Error saat mengecek dependency: {str(e)}')

@quran_index_bp.route('/excel/sheets', methods=['POST'])
def get_excel_sheets_endpoint():
    """
    Endpoint untuk mendapatkan daftar sheet dari file Excel yang diupload
    """
    try:
        if 'file' not in request.files:
            return error_response(400, 'Tidak ada file yang dikirim')
        
        file = request.files['file']
        
        if file.filename == '':
            return error_response(400, 'Tidak ada file yang dipilih')
        
        if not file.filename.endswith(('.xls', '.xlsx')):
            return error_response(400, 'File harus berformat Excel (.xls atau .xlsx)')
        
        # Simpan file sementara dengan timestamp untuk mencegah konflik nama file
        timestamp = int(time.time())
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{timestamp}_{secure_filename(file.filename)}")
        
        try:
            # Simpan file ke tempat sementara
            file.save(temp_path)
            
            # Cek apakah file berhasil disimpan
            if not os.path.exists(temp_path):
                return error_response(500, 'Gagal menyimpan file sementara')
            
            # Gunakan fungsi dari excel_importer.py
            try:
                success, result = get_excel_sheets(temp_path)
                
                if success:
                    return create_response(
                        data=result,
                        message='Daftar sheet berhasil diambil'
                    )
                else:
                    return error_response(500, result)
            except ImportError as e:
                # Fallback jika pandas tidak tersedia
                return error_response(500, f'Dependency tidak tersedia: {str(e)}. Pastikan pandas terinstall.')
            except Exception as e:
                return error_response(500, f'Error saat membaca file Excel: {str(e)}')
                
        except Exception as e:
            return error_response(500, f'Error saat memproses file: {str(e)}')
        finally:
            # Coba hapus file sementara
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Tidak dapat menghapus file sementara: {str(e)}")
    except Exception as e:
        return error_response(500, f'Error saat memproses file Excel: {str(e)}')

@quran_index_bp.route('/ayat/<int:index_id>', methods=['PUT'])
def update_index_ayat(index_id):
    """
    Endpoint untuk memperbarui daftar ayat untuk sebuah index
    Memerlukan autentikasi sebagai admin
    """
    try:
        if 'user_id' not in session:
            return error_response(401, 'Anda harus login untuk mengakses fitur ini')
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return error_response(403, 'Anda tidak memiliki akses untuk fitur ini')
        
        data = request.json
        
        if not data or 'ayat_list' not in data:
            return error_response(400, 'Data tidak lengkap, ayat_list harus diberikan')
        
        # Periksa apakah index ada
        index = get_quran_index_by_id(index_id)
        if not index:
            return error_response(404, 'Index tidak ditemukan')
        
        # Update list_ayat
        success, message = update_quran_index_ayat(index_id, data['ayat_list'])
        
        if success:
            return create_response(message=message)
        else:
            return error_response(500, message)
    except Exception as e:
        return error_response(500, f'Error saat memperbarui daftar ayat: {str(e)}') 