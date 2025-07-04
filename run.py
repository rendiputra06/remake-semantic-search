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
    update_model_status
)
from app.admin import admin_bp 
from app.auth import auth_bp
from app.public import public_bp
from app.auth.decorators import login_required, admin_required
from backend.monitoring import monitoring_bp
from app.api import init_app as init_api
from app.api.routes.ontology import ontology_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with proper config

# Register blueprints with proper URL prefixes
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(public_bp, url_prefix='')
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
app.register_blueprint(ontology_bp, url_prefix='/api/ontology')

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
    
    return render_template('settings.html', 
                         user=user,
                         settings=user_settings,
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

@app.route('/admin')
@admin_required
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
    
    # Cek status lexical database
    lexical_status = {
        'initialized': False,
        'last_updated': None,
        'entry_count': 0
    }
    
    try:
        lexical_status_file = os.path.join(os.path.dirname(__file__), 'database', 'lexical_status.json')
        if os.path.exists(lexical_status_file):
            with open(lexical_status_file, 'r') as f:
                lexical_status = json.load(f)
    except:
        pass
    
    # Cek status tesaurus
    thesaurus_status = {
        'initialized': False,
        'last_updated': None,
        'word_count': 0,
        'relation_count': 0
    }
    
    try:
        thesaurus_status_file = os.path.join(os.path.dirname(__file__), 'database', 'thesaurus_status.json')
        if os.path.exists(thesaurus_status_file):
            with open(thesaurus_status_file, 'r') as f:
                thesaurus_status = json.load(f)
    except:
        pass
    
    # Dapatkan daftar wordlist yang tersedia
    wordlist_files = []
    wordlist_dir = os.path.join(os.path.dirname(__file__), 'database', 'wordlists')
    
    if os.path.exists(wordlist_dir):
        for file in os.listdir(wordlist_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(wordlist_dir, file)
                file_size = os.path.getsize(file_path)
                file_created = datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Format ukuran file
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                wordlist_files.append({
                    'name': file,
                    'size': size_str,
                    'created': file_created
                })
    
    conn.close()
    
    return render_template('admin.html', users=users, model_status=model_status, 
                          lexical_status=lexical_status, thesaurus_status=thesaurus_status,
                          wordlist_files=wordlist_files)

@app.route('/run_lexical_command', methods=['POST'])
@admin_required
def run_lexical_command():
    """Menjalankan perintah terkait database lexical atau tesaurus"""
    command = request.form.get('command')
    
    valid_commands = {
        'init_lexical': ['scripts/init_lexical.py', '--component=lexical'],
        'init_thesaurus': ['scripts/init_lexical.py', '--component=thesaurus'],
        'export_lexical': ['scripts/export_lexical.py', '--type=lexical'],
        'export_thesaurus': ['scripts/export_lexical.py', '--type=all_relations']
    }
    
    if command not in valid_commands:
        flash(f'Perintah tidak valid: {command}', 'danger')
        return redirect(url_for('admin'))
    
    script_args = valid_commands[command]
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), script_args[0]))
    
    try:
        cmd = ['python', script_path]
        if len(script_args) > 1:
            cmd.extend(script_args[1:])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            flash(f'Perintah {command} berhasil dijalankan: {result.stdout}', 'success')
        else:
            flash(f'Error saat menjalankan perintah {command}: {result.stderr}', 'danger')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/run_wordlist_generator', methods=['POST'])
@admin_required
def run_wordlist_generator():
    """Menjalankan generator wordlist"""
    # Mengatur parameter
    output_filename = request.form.get('output_filename', f'wordlist_{datetime.datetime.now().strftime("%Y%m%d")}.txt')
    min_word_length = request.form.get('min_word_length', '3')
    min_word_freq = request.form.get('min_word_freq', '2')
    stem_words = 'stem_words' in request.files
    use_quran_dataset = 'use_quran_dataset' in request.form
    use_custom_txt = 'use_custom_txt' in request.form
    
    # Pastikan direktori wordlist ada
    wordlist_dir = os.path.join(os.path.dirname(__file__), 'database', 'wordlists')
    os.makedirs(wordlist_dir, exist_ok=True)
    
    output_path = os.path.join(wordlist_dir, output_filename)
    
    # Simpan file teks kustom jika ada
    custom_txt_paths = []
    if use_custom_txt and 'custom_txt_file' in request.files:
        custom_txt_files = request.files.getlist('custom_txt_file')
        
        if custom_txt_files:
            temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            for file in custom_txt_files:
                if file.filename:
                    safe_filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, safe_filename)
                    file.save(file_path)
                    custom_txt_paths.append(file_path)
    
    # Siapkan perintah untuk menjalankan script
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts/wordlist_generator.py'))
    cmd = ['python', script_path]
    
    # Tambahkan argumen berdasarkan parameter
    cmd.extend(['--output', output_path])
    cmd.extend(['--min-length', min_word_length])
    cmd.extend(['--min-frequency', min_word_freq])
    
    if stem_words:
        cmd.append('--stem')
    
    if use_quran_dataset:
        dataset_dir = os.path.join(os.path.dirname(__file__), 'dataset')
        cmd.extend(['--quran-dataset', dataset_dir])
    
    if custom_txt_paths:
        cmd.extend(['--input-dir', os.path.dirname(custom_txt_paths[0])])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Hapus file sementara
        for path in custom_txt_paths:
            if os.path.exists(path):
                os.remove(path)
        
        if result.returncode == 0:
            flash(f'Wordlist berhasil dibuat: {output_filename}', 'success')
        else:
            flash(f'Error saat membuat wordlist: {result.stderr}', 'danger')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/download_wordlist/<filename>')
@admin_required
def download_wordlist(filename):
    """Download file wordlist"""
    wordlist_dir = os.path.join(os.path.dirname(__file__), 'database', 'wordlists')
    return send_file(os.path.join(wordlist_dir, filename), as_attachment=True)

@app.route('/delete_wordlist', methods=['POST'])
@admin_required
def delete_wordlist():
    """Menghapus file wordlist"""
    filename = request.form.get('filename')
    
    if not filename:
        return jsonify({
            'success': False,
            'message': 'Nama file tidak disediakan'
        })
    
    wordlist_dir = os.path.join(os.path.dirname(__file__), 'database', 'wordlists')
    file_path = os.path.join(wordlist_dir, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': f'File {filename} berhasil dihapus'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'File {filename} tidak ditemukan'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/import_lexical_data', methods=['POST'])
@admin_required
def import_lexical_data():
    """Mengimpor data lexical dari file CSV/Excel"""
    if 'lexical_file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin'))
    
    file = request.files['lexical_file']
    
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin'))
    
    overwrite = 'overwrite' in request.form
    
    try:
        # Simpan file sementara
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)
        
        # Jalankan script impor
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts/import_lexical.py'))
        cmd = ['python', script_path, file_path]
        
        if overwrite:
            cmd.append('--overwrite')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Hapus file sementara
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result.returncode == 0:
            flash('Data lexical berhasil diimpor', 'success')
        else:
            flash(f'Error saat mengimpor data: {result.stderr}', 'danger')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/import_thesaurus_data', methods=['POST'])
@admin_required
def import_thesaurus_data():
    """Mengimpor data tesaurus dari file CSV/Excel"""
    if 'thesaurus_file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin'))
    
    file = request.files['thesaurus_file']
    
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin'))
    
    relation_type = request.form.get('relation_type', 'synonym')
    overwrite = 'overwrite' in request.form
    
    try:
        # Simpan file sementara
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)
        
        # Jalankan script impor
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts/import_thesaurus.py'))
        cmd = ['python', script_path, file_path, '--type', relation_type]
        
        if overwrite:
            cmd.append('--overwrite')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Hapus file sementara
        if os.path.exists(file_path):
            os.remove(file_path)
        
        if result.returncode == 0:
            flash(f'Data relasi {relation_type} berhasil diimpor', 'success')
        else:
            flash(f'Error saat mengimpor data: {result.stderr}', 'danger')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin'))

@app.route('/api/thesaurus/enrich', methods=['POST'])
@admin_required
def api_thesaurus_enrich():
    """API untuk pengayaan tesaurus menggunakan wordlist"""
    wordlist_name = request.form.get('wordlist')
    relation_type = request.form.get('relation_type', 'synonym')
    min_score = float(request.form.get('min_score', 0.7))
    max_relations = int(request.form.get('max_relations', 5))
    
    if not wordlist_name:
        return jsonify({
            'success': False,
            'message': 'Nama wordlist harus disediakan'
        })
    
    # Tentukan path ke file wordlist
    wordlist_dir = os.path.join(os.path.dirname(__file__), 'database', 'wordlists')
    wordlist_path = os.path.join(wordlist_dir, wordlist_name)
    
    if not os.path.exists(wordlist_path):
        return jsonify({
            'success': False,
            'message': f'Wordlist tidak ditemukan: {wordlist_name}'
        })
    
    try:
        # Jalankan script pengayaan tesaurus
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts/enrich_thesaurus.py'))
        command = [
            'python', script_path,
            '--wordlist', wordlist_path,
            '--type', relation_type,
            '--min-score', str(min_score),
            '--max-relations', str(max_relations)
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Pengayaan tesaurus berhasil',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error saat menjalankan proses pengayaan',
                'error': result.stderr
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/thesaurus/visualize')
@admin_required
def api_thesaurus_visualize():
    """API untuk visualisasi tesaurus"""
    word = request.args.get('word')
    depth = int(request.args.get('depth', 2))
    
    if not word:
        return jsonify({
            'success': False,
            'message': 'Parameter kata harus disediakan'
        })
    
    try:
        # Koneksi ke database
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'lexical.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Cari ID kata
        cursor.execute("SELECT id FROM lexical WHERE word = ?", (word,))
        word_result = cursor.fetchone()
        
        if not word_result:
            return jsonify({
                'success': False,
                'message': f'Kata "{word}" tidak ditemukan dalam database'
            })
        
        word_id = word_result['id']
        
        # Struktur data untuk respons
        nodes = []
        edges = []
        
        # Tambahkan node utama
        nodes.append({
            'id': word_id,
            'label': word,
            'group': 'main'
        })
        
        # Fungsi untuk mendapatkan relasi
        def get_relations(source_id, current_depth, max_depth):
            if current_depth > max_depth:
                return
            
            # Sinonim
            cursor.execute("""
            SELECT l.id, l.word, s.strength, 'synonym' as type
            FROM synonyms s
            JOIN lexical l ON s.synonym_id = l.id
            WHERE s.word_id = ?
            """, (source_id,))
            synonyms = cursor.fetchall()
            
            # Antonim
            cursor.execute("""
            SELECT l.id, l.word, a.strength, 'antonym' as type
            FROM antonyms a
            JOIN lexical l ON a.antonym_id = l.id
            WHERE a.word_id = ?
            """, (source_id,))
            antonyms = cursor.fetchall()
            
            # Hiponim
            cursor.execute("""
            SELECT l.id, l.word, 1.0 as strength, 'hyponym' as type
            FROM hyponyms h
            JOIN lexical l ON h.hyponym_id = l.id
            WHERE h.word_id = ?
            """, (source_id,))
            hyponyms = cursor.fetchall()
            
            # Hipernim
            cursor.execute("""
            SELECT l.id, l.word, 1.0 as strength, 'hypernym' as type
            FROM hypernyms h
            JOIN lexical l ON h.hypernym_id = l.id
            WHERE h.word_id = ?
            """, (source_id,))
            hypernyms = cursor.fetchall()
            
            # Gabungkan semua relasi
            all_relations = synonyms + antonyms + hyponyms + hypernyms
            
            # Tambahkan ke graf
            for relation in all_relations:
                target_id = relation['id']
                
                # Cek apakah node sudah ada
                node_exists = any(node['id'] == target_id for node in nodes)
                if not node_exists:
                    nodes.append({
                        'id': target_id,
                        'label': relation['word'],
                        'group': relation['type']
                    })
                
                # Tambahkan edge
                edge_id = f"{source_id}-{target_id}"
                edge_exists = any(edge['id'] == edge_id for edge in edges)
                if not edge_exists:
                    edges.append({
                        'id': edge_id,
                        'from': source_id,
                        'to': target_id,
                        'label': relation['type'],
                        'type': relation['type'],
                        'strength': relation['strength']
                    })
                
                # Rekursif untuk level berikutnya
                if current_depth < max_depth:
                    get_relations(target_id, current_depth + 1, max_depth)
        
        # Mulai mencari relasi
        get_relations(word_id, 1, depth)
        
        return jsonify({
            'success': True,
            'nodes': nodes,
            'edges': edges
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })
    finally:
        if conn:
            conn.close()

@app.route('/api/thesaurus/search')
@admin_required
def api_thesaurus_search():
    """API untuk pencarian kata dalam tesaurus"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'message': 'Query pencarian terlalu pendek'
        })
    
    try:
        # Koneksi ke database
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'lexical.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Cari kata yang cocok dengan query
        cursor.execute("""
        SELECT id, word, definition, example
        FROM lexical
        WHERE word LIKE ?
        LIMIT 20
        """, (f"%{query}%",))
        
        results = []
        for row in cursor.fetchall():
            word_id = row['id']
            word = row['word']
            definition = row['definition'] or ""
            example = row['example'] or ""
            
            # Hitung jumlah relasi
            cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM synonyms WHERE word_id = ?) as synonym_count,
                (SELECT COUNT(*) FROM antonyms WHERE word_id = ?) as antonym_count,
                (SELECT COUNT(*) FROM hyponyms WHERE word_id = ?) as hyponym_count,
                (SELECT COUNT(*) FROM hypernyms WHERE word_id = ?) as hypernym_count
            """, (word_id, word_id, word_id, word_id))
            
            rel_counts = cursor.fetchone()
            
            results.append({
                'id': word_id,
                'word': word,
                'definition': definition,
                'example': example,
                'relations': {
                    'synonym': rel_counts['synonym_count'],
                    'antonym': rel_counts['antonym_count'],
                    'hyponym': rel_counts['hyponym_count'],
                    'hypernym': rel_counts['hypernym_count']
                }
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })
    finally:
        if conn:
            conn.close()

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
    app.run(debug=True, port=5000)
