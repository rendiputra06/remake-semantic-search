"""
Helper functions and utilities for authentication.
"""
from functools import wraps
from flask import session

def get_current_user():
    """Get the currently logged in user's data."""
    if 'user_id' in session:
        return {
            'id': session['user_id'],
            'username': session.get('username'),
            'role': session.get('role')
        }
    return None

def is_authenticated():
    """Check if the current user is authenticated."""
    return 'user_id' in session

def is_admin():
    """Check if the current user is an admin."""
    return session.get('role') == 'admin'

# Additional utility functions can be added here
