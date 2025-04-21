from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
from functools import wraps
import os
import subprocess
from backend.api import api_bp
from backend.db import init_db, get_user_by_id, get_user_by_username, authenticate_user, register_user
from backend.db import get_user_settings, update_user_settings, add_search_history, get_search_history
from backend.db import get_model_status, update_model_status, get_db_connection
from backend.monitoring import monitoring_bp  # Import monitoring blueprint

app = Flask(__name__)
app.secret_key = 'rahasia_semantic_search' # Ganti dengan secret key yang lebih aman di produksi
CORS(app)  # Mengaktifkan CORS untuk semua domain

# Registrasi blueprint API
app.register_blueprint(api_bp, url_prefix='/api')

# Daftarkan blueprint monitoring
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')

# Inisialisasi database
init_db()

# Decorator untuk halaman yang membutuhkan autentikasi
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator untuk halaman yang membutuhkan akses admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Halaman utama mesin pencarian."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Halaman tentang aplikasi."""
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
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
    
    return render_template('login.html')

# @app.route('/register', methods=['GET', 'POST'])
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
#             return render_template('register.html')
        
#         success, message = register_user(username, password, email)
        
#         if success:
#             flash(message, 'success')
#             return redirect(url_for('login'))
#         else:
#             flash(message, 'danger')
    
#     return render_template('register.html')

@app.route('/logout')
def logout():
    """Proses logout."""
    session.clear()
    flash('Anda telah keluar dari sistem.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """Halaman profil pengguna."""
    user = get_user_by_id(session['user_id'])
    user_settings = get_user_settings(session['user_id'])
    search_history = get_search_history(session['user_id'])
    
    return render_template('profile.html', user=user, settings=user_settings, history=search_history)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Halaman pengaturan."""
    user = get_user_by_id(session['user_id'])
    user_settings = get_user_settings(session['user_id'])
    model_status = get_model_status()
    
    if request.method == 'POST':
        default_model = request.form.get('default_model')
        result_limit = int(request.form.get('result_limit'))
        threshold = float(request.form.get('threshold'))
        
        success, message = update_user_settings(session['user_id'], default_model, result_limit, threshold)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=user, settings=user_settings, model_status=model_status)

@app.route('/initialize_model', methods=['POST'])
@login_required
def initialize_model():
    """Memulai inisialisasi model."""
    model_name = request.form.get('model_name')
    
    if model_name not in ['word2vec', 'fasttext', 'glove']:
        flash('Model tidak valid.', 'danger')
        return redirect(url_for('settings'))
    
    try:
        # Jalankan proses inisialisasi di background
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'scripts/init_{model_name}.py'))
        subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Update status model
        update_model_status(model_name, True)
        
        flash(f'Inisialisasi model {model_name.upper()} sedang berjalan di latar belakang.', 'success')
    except Exception as e:
        flash(f'Error saat menginisialisasi model: {str(e)}', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/admin')
@login_required
def admin():
    
    # Ambil daftar user
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, email, role, created_at, last_login FROM users').fetchall()
    
    # Cek status model
    model_status = {}
    for model_name in ['qa_model', 'semantic_model', 'search_model']:
        model_status[model_name] = {
            'initialized': True,  # Ganti dengan pengecekan status asli
            'last_updated': '2023-01-01 00:00:00'  # Ganti dengan data timestamp asli
        }
    
    conn.close()
    
    return render_template('admin.html', users=users, model_status=model_status)

@app.route('/quran-index')
def quran_index():
    """Halaman klasifikasi index Al-Quran."""
    return render_template('quran_index.html')

@app.route('/api/statistics')
@login_required
def get_statistics():
    
    conn = get_db_connection()
    
    # Hitung total indeks
    total_indexes = conn.execute('SELECT COUNT(*) FROM quran_index').fetchone()[0]
    
    # Hitung total ayat
    total_verses = conn.execute('SELECT COUNT(*) FROM quran_ayat').fetchone()[0]
    
    # Hitung indeks dengan ayat
    indexes_with_verses = conn.execute('''
        SELECT COUNT(DISTINCT index_id) FROM quran_ayat
    ''').fetchone()[0]
    
    # Hitung indeks root
    root_indexes = conn.execute('''
        SELECT COUNT(*) FROM quran_index
        WHERE parent_id IS NULL
    ''').fetchone()[0]
    
    # Statistik berdasarkan level
    level_stats = conn.execute('''
        SELECT level, COUNT(*) as count FROM quran_index
        GROUP BY level ORDER BY level
    ''').fetchall()
    
    # Surah yang paling banyak diindeks
    top_surahs = conn.execute('''
        SELECT surah as surah_id, 
               'Surah ' || surah as surah_name, 
               COUNT(*) as verse_count
        FROM quran_ayat
        GROUP BY surah
        ORDER BY verse_count DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'total_categories': total_indexes,
        'total_verses': total_verses,
        'categories_with_ayat': indexes_with_verses,
        'root_categories': root_indexes,
        'level_stats': [dict(row) for row in level_stats],
        'surah_stats': [dict(row) for row in top_surahs]
    })

@app.context_processor
def inject_user():
    """Menyediakan data user untuk semua template."""
    if 'user_id' in session:
        user_data = {
            'id': session['user_id'], 
            'username': session.get('username'), 
            'role': session.get('role'),
            'settings': get_user_settings(session['user_id'])
        }
        return {'user': user_data}
    return {'user': None}

if __name__ == '__main__':
    app.run(debug=True, port=7000)
