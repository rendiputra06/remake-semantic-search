"""
Public Thesaurus routes for the semantic search API.
"""
from flask import Blueprint, request
from marshmallow import ValidationError

from ..utils import create_response, error_response, validation_error_response
from ..services.public_thesaurus_service import PublicThesaurusService
from app.api.schemas.public_thesaurus import (
    ThesaurusSearchSchema,
    ThesaurusBrowseSchema,
    ThesaurusRandomSchema,
    ThesaurusPopularSchema
)

public_thesaurus_bp = Blueprint('public_thesaurus', __name__)
service = PublicThesaurusService()

@public_thesaurus_bp.route('/search', methods=['GET'])
def search():
    """Public endpoint for searching thesaurus data."""
    try:
        # Validate request parameters
        schema = ThesaurusSearchSchema()
        data = schema.load(request.args)
        
        word = data['word']
        results = service.search_word(word)
        
        return create_response(
            data={'results': results},
            message='Pencarian tesaurus berhasil'
        )
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

@public_thesaurus_bp.route('/browse', methods=['GET'])
def browse():
    """Public endpoint for browsing thesaurus data."""
    try:
        # Validate request parameters
        schema = ThesaurusBrowseSchema()
        data = schema.load(request.args)
        
        results = service.browse_words(
            page=data['page'],
            per_page=data['per_page'],
            sort_by=data['sort_by'],
            filter_type=data['filter_type']
        )
        
        return create_response(
            data=results,
            message='Browsing tesaurus berhasil'
        )
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

@public_thesaurus_bp.route('/statistics', methods=['GET'])
def statistics():
    """Public endpoint for thesaurus statistics."""
    try:
        stats = service.get_statistics()
        
        return create_response(
            data=stats,
            message='Statistik tesaurus berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

@public_thesaurus_bp.route('/random', methods=['GET'])
def random_words():
    """Public endpoint for random words."""
    try:
        # Validate request parameters
        schema = ThesaurusRandomSchema()
        data = schema.load(request.args)
        
        words = service.get_random_words(data['count'])
        
        return create_response(
            data={'words': words},
            message='Kata acak berhasil diambil'
        )
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

@public_thesaurus_bp.route('/popular', methods=['GET'])
def popular_words():
    """Public endpoint for popular words."""
    try:
        # Validate request parameters
        schema = ThesaurusPopularSchema()
        data = schema.load(request.args)
        
        words = service.get_popular_words(data['limit'])
        
        return create_response(
            data={'words': words},
            message='Kata populer berhasil diambil'
        )
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, f'Error: {str(e)}')

@public_thesaurus_bp.route('/suggestions', methods=['GET'])
def search_suggestions():
    """Public endpoint for search suggestions."""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return create_response(
                data={'suggestions': []},
                message='Query terlalu pendek'
            )
        
        suggestions = service.search_suggestions(query, limit)
        
        return create_response(
            data={'suggestions': suggestions},
            message='Saran pencarian berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, f'Error: {str(e)}') 