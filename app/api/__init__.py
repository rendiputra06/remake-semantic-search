"""
API package initialization and blueprint registration.
"""
from flask import Blueprint, jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

# Import blueprints
from .routes.search import search_bp
from .routes.statistics import stats_bp
from .routes.thesaurus import thesaurus_bp
from .routes.public_thesaurus import public_thesaurus_bp
from .routes.export import export_bp
from .routes.models import models_bp
from .routes.quran_index import quran_index_bp
from .routes.quran import quran_bp
from .routes.public_quran import public_quran_bp
from .routes.query import query_bp
from .routes.evaluation import evaluation_bp
from .routes.evaluation_v2 import evaluation_v2_bp
from .routes.evaluation_v3 import evaluation_v3_bp
from .routes.asr_quran import asr_quran_bp

from .utils import error_response, validation_error_response

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Register sub-blueprints
def init_app(app):
    """
    Initialize API blueprints with the Flask application
    """
    # Register all blueprints with URL prefixes
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(stats_bp, url_prefix='/api/statistics')
    app.register_blueprint(thesaurus_bp, url_prefix='/api/thesaurus')
    app.register_blueprint(public_thesaurus_bp, url_prefix='/api/public/thesaurus')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(models_bp, url_prefix='/api/models')
    app.register_blueprint(quran_index_bp, url_prefix='/api/quran-index')
    app.register_blueprint(quran_bp, url_prefix='/api/quran')
    app.register_blueprint(public_quran_bp, url_prefix='/api/public/quran')
    app.register_blueprint(query_bp, url_prefix='/api/query')
    app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')
    app.register_blueprint(evaluation_v2_bp, url_prefix='/api/evaluation-v2')
    app.register_blueprint(evaluation_v3_bp, url_prefix='/api/evaluation_v3')
    app.register_blueprint(asr_quran_bp, url_prefix='/api/asr_quran')

    # Register error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return validation_error_response(error.messages)

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': 'Resource tidak ditemukan'
        }), 404

    @app.errorhandler(400)
    def bad_request_error(error):
        return error_response(400, str(error))
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            'success': False,
            'message': 'Tidak terotorisasi'
        }), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            'success': False,
            'message': 'Akses ditolak'
        }), 403

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan internal server'
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return error_response(500, str(error))
