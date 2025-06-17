"""
Authentication decorators for the application.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from backend.db import get_user_by_id

def error_response(status_code, message=None):
    """Create an error response for API endpoints."""
    from werkzeug.http import HTTP_STATUS_CODES
    payload = {
        'success': False,
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'message': message,
        'data': None
    }
    return jsonify(payload), status_code

def login_required(f):
    """Decorator untuk halaman yang membutuhkan autentikasi."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator untuk halaman yang membutuhkan akses admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required_api(f):
    """Decorator untuk API endpoint yang membutuhkan akses admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return error_response(401, 'Anda harus login untuk mengakses fitur ini')
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return error_response(403, 'Anda tidak memiliki akses untuk fitur ini')
        
        return f(*args, **kwargs)
    return decorated_function
