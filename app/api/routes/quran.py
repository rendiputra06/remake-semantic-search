"""
Quran related routes for the semantic search API.
"""
from flask import Blueprint, request
from backend.db import get_all_surah, get_surah_by_number, get_verses_by_surah
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