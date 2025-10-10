from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import os
import json
import datetime
import sqlite3
import subprocess
from werkzeug.utils import secure_filename

from backend.db import (
    get_db_connection, init_db, get_user_by_id, get_user_settings,
    get_search_history, update_user_settings, get_model_status,
    update_model_status, get_global_thresholds, update_global_thresholds
)
from app.admin import admin_bp 
from app.auth import auth_bp
from app.public import public_bp
from app.auth.decorators import login_required, admin_required
from backend.monitoring import monitoring_bp
from app.api import init_app as init_api
from app.api.routes.ontology import ontology_bp
from app.dual_search import blueprint as dual_search_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with proper config

# Register blueprints with proper URL prefixes
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(public_bp, url_prefix='')
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
app.register_blueprint(ontology_bp, url_prefix='/api/ontology')
app.register_blueprint(dual_search_bp, url_prefix='/dual-search')

# Initialize API routes
init_api(app)

# Initialize database
init_db()

@app.route('/')
def index():
    """Main search engine page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        user_settings = get_user_settings(session['user_id'])
        search_history = get_search_history(session['user_id'])
        user['settings'] = user_settings
    
    return render_template('index.html', user=user)

@app.route('/health')
def health():
    """Health check endpoint untuk Docker."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

@app.route('/about')
def about():
    """About page."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    
    return render_template('about.html', user=user)

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    user = get_user_by_id(session['user_id'])
    user_settings = get_user_settings(session['user_id'])
    search_history = get_search_history(session['user_id'])
    
    return render_template('profile.html', 
                         user=user, 
                         settings=user_settings,
                         search_history=search_history)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page."""
    user = get_user_by_id(session['user_id'])
    model_status = get_model_status()
    model_list = ['word2vec', 'fasttext', 'glove', 'ensemble', 'ontology']
    model_names = {
        'word2vec': 'Word2Vec',
        'fasttext': 'FastText',
        'glove': 'GloVe',
        'ensemble': 'Ensemble',
        'ontology': 'Ontologi'
    }
    thresholds = get_global_thresholds()

    if request.method == 'POST':
        # Ambil threshold per model dari form
        new_thresholds = {}
        for model in model_list:
            val = request.form.get(f'threshold_{model}')
            try:
                val = float(val)
            except Exception:
                val = 0.5
            new_thresholds[model] = val
        success = update_global_thresholds(new_thresholds)
        if success:
            flash('Pengaturan threshold per model berhasil diperbarui.', 'success')
        else:
            flash('Gagal memperbarui threshold. Pastikan nilai antara 0 dan 1.', 'danger')
        return redirect(url_for('settings'))

    return render_template('settings.html', 
                         user=user,
                         thresholds=thresholds,
                         model_list=model_list,
                         model_names=model_names,
                         model_status=model_status)

@app.route('/initialize_model', methods=['POST'])
@login_required
def initialize_model():
    """Initialize a model."""
    model_name = request.form.get('model_name')
    
    if not model_name:
        flash('Model tidak ditemukan.', 'danger')
        return redirect(url_for('settings'))
    
    try:
        script_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            'scripts',
            f'init_{model_name}.py'
        ))
        
        if os.path.exists(script_path):
            # Run the initialization script
            process = subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Update model status
                update_model_status(model_name, True)
                flash(f'Model {model_name} berhasil diinisialisasi.', 'success')
            else:
                flash(f'Error saat menginisialisasi model {model_name}: {stderr.decode()}', 'danger')
        else:
            flash(f'Script inisialisasi tidak ditemukan untuk model {model_name}.', 'danger')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/ontology')
def ontology_search():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('ontology_search.html', user=user)

@app.route('/ontology-info')
def ontology_info():
    """Halaman informasi detail tentang pencarian ontologi."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('info.html', user=user)

@app.route('/admin/ontology')
@admin_required
def ontology_admin():
    user = get_user_by_id(session['user_id']) if 'user_id' in session else None
    return render_template('ontology_admin.html', user=user)

@app.route('/ontology-trace')
def ontology_trace():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('ontology_trace.html', user=user)

@app.route('/ontology-visualization')
def ontology_visualization():
    """Halaman visualisasi ontologi untuk public"""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('ontology_visualization.html', user=user)

@app.route('/ensemble-analysis')
def ensemble_analysis():
    """Halaman analisis model ensemble"""
    return render_template('ensemble_analysis.html')

@app.route('/quran-index')
def quran_index():
    """Halaman klasifikasi index Al-Quran."""
    return render_template('quran_index.html')

@app.route('/labs')
@admin_required
def labs():
    """Halaman Labs (admin-only) untuk mengakses fitur yang disembunyikan dari UI utama."""
    return render_template('labs.html')

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
    app.run(debug=True, port=5000, host='0.0.0.0')
