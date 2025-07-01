"""
Quran related routes for the semantic search API.
"""
from flask import Blueprint, request, jsonify
from backend.db import get_all_surah, get_surah_by_number, get_verses_by_surah, get_verse_by_id, get_db_connection
from ..utils import create_response, error_response

quran_bp = Blueprint('quran', __name__)

@quran_bp.route('/surah', methods=['GET'])
def get_all_surah_list():
    """
    Endpoint untuk mendapatkan daftar semua surah Al-Quran
    """
    try:
        surah_list = get_all_surah()
        
        return create_response(
            data=surah_list,
            message='Daftar surah berhasil diambil'
        )
    except Exception as e:
        return error_response(500, f'Error saat mendapatkan daftar surah: {str(e)}')

@quran_bp.route('/surah/<int:surah_number>', methods=['GET'])
def get_surah_detail(surah_number):
    """
    Endpoint untuk mendapatkan detail surah dan ayatnya
    """
    try:
        # Dapatkan informasi surah
        surah = get_surah_by_number(surah_number)
        
        if not surah:
            return error_response(404, f'Surah dengan nomor {surah_number} tidak ditemukan')
        
        # Dapatkan ayat-ayat dari surah ini
        verses = get_verses_by_surah(surah_number)
        
        return create_response(
            data={
                'surah': surah,
                'verses': verses
            },
            message='Detail surah berhasil diambil'
        )
    except Exception as e:
        return error_response(500, f'Error saat mendapatkan detail surah: {str(e)}')

@quran_bp.route('/ayat_detail')
def ayat_detail():
    surah = request.args.get('surah')
    ayat = request.args.get('ayat')
    if not surah or not ayat:
        return jsonify({'success': False, 'message': 'Parameter surah dan ayat wajib diisi'})
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.id, v.surah_id, v.surah_name, v.verse_number, v.verse_text, v.verse_translation, s.surah_name as surah_name, s.surah_name_en
            FROM quran_verses v
            JOIN quran_surah s ON v.surah_id = s.surah_number
            WHERE v.surah_id = ? AND v.verse_number = ?
        ''', (int(surah), int(ayat)))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'Ayat tidak ditemukan'})
        ayat_data = {
            'id': row['id'],
            'surah': row['surah_id'],
            'surah_name': row['surah_name'],
            'ayat': row['verse_number'],
            'text': row['verse_text'],
            'translation': row['verse_translation']
        }
        return jsonify({'success': True, 'ayat': ayat_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}) 