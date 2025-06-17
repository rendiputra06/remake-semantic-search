"""
Statistics service implementation.
"""
from typing import Dict, List, Optional
from datetime import datetime
from backend.db import get_db_connection, get_app_statistics, get_overall_statistics

class StatisticsService:
    """Service class for handling statistics operations."""
    
    def get_overall_stats(self) -> Dict:
        """Get overall application statistics."""
        try:
            # Get overall statistics
            overall_stats = get_overall_statistics()
            
            # Get last 30 days statistics for trends
            daily_stats = get_app_statistics()
            
            # Format daily stats for chart
            dates = []
            searches = []
            users = []
            
            for stat in daily_stats:
                dates.append(stat['date'])
                searches.append(stat['total_searches'])
                users.append(stat['unique_users'])
            
            return {
                'success': True,
                'data': {
                    'overall': overall_stats,
                    'trends': {
                        'dates': dates,
                        'searches': searches,
                        'users': users
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mendapatkan statistik keseluruhan: {str(e)}'
            }
    
    def get_daily_stats(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict:
        """Get daily statistics."""
        try:
            daily_stats = get_app_statistics(start_date, end_date)
            
            return {
                'success': True,
                'data': daily_stats
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mendapatkan statistik harian: {str(e)}'
            }
    
    def get_model_usage_stats(self) -> Dict:
        """Get model usage statistics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get model usage counts
            cursor.execute('''
                SELECT model, COUNT(*) as count
                FROM search_history
                WHERE model IS NOT NULL
                GROUP BY model
            ''')
            
            model_stats = {}
            for row in cursor.fetchall():
                model_stats[row['model']] = row['count']
            
            conn.close()
            
            return {
                'success': True,
                'data': model_stats
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mendapatkan statistik penggunaan model: {str(e)}'
            }
    
    def get_search_performance_stats(self) -> Dict:
        """Get search performance statistics."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get average results per model
            cursor.execute('''
                SELECT model, 
                       AVG(result_count) as avg_results,
                       MIN(result_count) as min_results,
                       MAX(result_count) as max_results
                FROM search_history
                WHERE model IS NOT NULL
                GROUP BY model
            ''')
            
            performance_stats = {}
            for row in cursor.fetchall():
                performance_stats[row['model']] = {
                    'avg_results': row['avg_results'],
                    'min_results': row['min_results'],
                    'max_results': row['max_results']
                }
            
            conn.close()
            
            return {
                'success': True,
                'data': performance_stats
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saat mendapatkan statistik performa pencarian: {str(e)}'
            }