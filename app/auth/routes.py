"""
Authentication routes for the application.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.db import authenticate_user, register_user, get_user_by_id

# Buat blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        success, result = authenticate_user(username, password)
        
        if success:
            session['user_id'] = result
            user = get_user_by_id(result)
            session['username'] = user['username']
            session['role'] = user['role']
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash(result, 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Proses logout."""
    session.clear()
    flash('Anda telah keluar dari sistem.', 'success')
    return redirect(url_for('index'))

# Route untuk registrasi (dinonaktifkan)
# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     """Halaman registrasi."""
#     if 'user_id' in session:
#         return redirect(url_for('index'))
    
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password')
#         confirm_password = request.form.get('confirm_password')
#         email = request.form.get('email')
        
#         if password != confirm_password:
#             flash('Password tidak cocok.', 'danger')
#             return render_template('auth/register.html')
        
#         success, message = register_user(username, password, email)
        
#         if success:
#             flash(message, 'success')
#             return redirect(url_for('auth.login'))
#         else:
#             flash(message, 'danger')
    
#     return render_template('auth/register.html')
