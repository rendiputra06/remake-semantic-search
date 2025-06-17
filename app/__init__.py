"""
Application package initialization.
"""
from .admin import blueprint as admin_bp
from .auth import blueprint as auth_bp
from .api import api_bp

# Export blueprints for use in the main app
__all__ = ['admin_bp', 'auth_bp', 'api_bp']
