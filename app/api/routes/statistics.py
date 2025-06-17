"""
Statistics related routes for the semantic search API.
"""
from flask import Blueprint, request
from backend.db import get_app_statistics, get_overall_statistics
from ..utils import create_response, error_response

stats_bp = Blueprint('statistics', __name__)

@stats_bp.route('/statistics/overall', methods=['GET'])
def get_app_overall_stats():
    """
    Mendapatkan statistik keseluruhan penggunaan aplikasi
    """
    try:
        # Ambil statistik keseluruhan
        overall_stats = get_overall_statistics()
        
        # Dapatkan statistik 30 hari terakhir untuk tren
        daily_stats = get_app_statistics()
        
        # Format daily_stats untuk chart
        dates = []
        searches = []
        users = []
        
        for stat in daily_stats:
            dates.append(stat['date'])
            searches.append(stat['total_searches'])
            users.append(stat['unique_users'])
        
        return create_response(
            data={
                'overall': overall_stats,
                'trends': {
                    'dates': dates,
                    'searches': searches,
                    'users': users
                }
            },
            message='Statistik keseluruhan berhasil diambil'
        )
    except Exception as e:
        return error_response(500, f'Error saat mendapatkan statistik keseluruhan: {str(e)}')

@stats_bp.route('/statistics/daily', methods=['GET'])
def get_app_daily_stats():
    """
    Mendapatkan statistik harian penggunaan aplikasi
    """
    try:
        # Dapatkan parameter query
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Ambil statistik berdasarkan parameter
        daily_stats = get_app_statistics(start_date, end_date)
        
        return create_response(
            data=daily_stats,
            message='Statistik harian berhasil diambil'
        )
    except Exception as e:
        return error_response(500, f'Error saat mendapatkan statistik harian: {str(e)}')