"""
Admin routes for the application.
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from backend.db import get_db_connection
from app.auth.decorators import admin_required
from .utils import (
    get_db_status, get_wordlist_files, run_lexical_command,
    run_wordlist_generator, import_lexical_data, import_thesaurus_data,
    enrich_thesaurus
)

# Create blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def admin():
    """Admin panel main page."""
    # Get user list
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, email, role, created_at, last_login FROM users').fetchall()
    
    # Get database and model status
    model_status, lexical_status, thesaurus_status = get_db_status()
    
    # Get available wordlists
    wordlist_files = get_wordlist_files()
    
    conn.close()
    
    return render_template('admin.html', 
                         users=users,
                         model_status=model_status, 
                         lexical_status=lexical_status, 
                         thesaurus_status=thesaurus_status,
                         wordlist_files=wordlist_files)

@admin_bp.route('/run_lexical_command', methods=['POST'])
@admin_required
def run_lexical_command_route():
    """Execute lexical database related commands."""
    command = request.form.get('command')
    
    try:
        result = run_lexical_command(command)
        if result.returncode == 0:
            flash(f'Perintah {command} berhasil dijalankan: {result.stdout}', 'success')
        else:
            flash(f'Error saat menjalankan perintah {command}: {result.stderr}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/run_wordlist_generator', methods=['POST'])
@admin_required
def run_wordlist_generator_route():
    """Run wordlist generator."""
    output_filename = request.form.get('output_filename', f'wordlist_{datetime.now().strftime("%Y%m%d")}.txt')
    min_word_length = request.form.get('min_word_length', '3')
    min_word_freq = request.form.get('min_word_freq', '2')
    stem_words = 'stem_words' in request.form
    use_quran_dataset = 'use_quran_dataset' in request.form
    use_custom_txt = 'use_custom_txt' in request.form
    custom_txt_files = request.files.getlist('custom_txt_file') if use_custom_txt else None
    
    try:
        result = run_wordlist_generator(
            output_filename=output_filename,
            min_word_length=min_word_length,
            min_word_freq=min_word_freq,
            stem_words=stem_words,
            use_quran_dataset=use_quran_dataset,
            use_custom_txt=use_custom_txt,
            custom_txt_files=custom_txt_files
        )
        
        if result.returncode == 0:
            flash(f'Wordlist berhasil dibuat: {output_filename}', 'success')
        else:
            flash(f'Error saat membuat wordlist: {result.stderr}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/download_wordlist/<filename>')
@admin_required
def download_wordlist(filename):
    """Download a wordlist file."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
    return send_file(
        os.path.join(wordlist_dir, filename),
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/delete_wordlist', methods=['POST'])
@admin_required
def delete_wordlist():
    """Delete a wordlist file."""
    filename = request.form.get('filename')
    
    if not filename:
        flash('Nama file tidak disediakan', 'danger')
        return redirect(url_for('admin.admin'))
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
    file_path = os.path.join(wordlist_dir, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'File {filename} berhasil dihapus', 'success')
        else:
            flash(f'File {filename} tidak ditemukan', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/import_lexical_data', methods=['POST'])
@admin_required
def import_lexical_data_route():
    """Import lexical data from CSV/Excel file."""
    if 'lexical_file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin.admin'))
    
    file = request.files['lexical_file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin.admin'))
    
    overwrite = 'overwrite' in request.form
    
    try:
        result = import_lexical_data(file, overwrite)
        if result.returncode == 0:
            flash('Data lexical berhasil diimpor', 'success')
        else:
            flash(f'Error saat mengimpor data: {result.stderr}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/import_thesaurus_data', methods=['POST'])
@admin_required
def import_thesaurus_data_route():
    """Import thesaurus data from CSV/Excel file."""
    if 'thesaurus_file' not in request.files:
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin.admin'))
    
    file = request.files['thesaurus_file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'danger')
        return redirect(url_for('admin.admin'))
    
    relation_type = request.form.get('relation_type', 'synonym')
    overwrite = 'overwrite' in request.form
    
    try:
        result = import_thesaurus_data(file, relation_type, overwrite)
        if result.returncode == 0:
            flash('Data tesaurus berhasil diimpor', 'success')
        else:
            flash(f'Error saat mengimpor data: {result.stderr}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/enrich_thesaurus', methods=['POST'])
@admin_required
def enrich_thesaurus_route():
    """Enrich thesaurus using wordlist."""
    wordlist = request.form.get('wordlist')
    if not wordlist:
        flash('Pilih wordlist yang akan digunakan', 'danger')
        return redirect(url_for('admin.admin'))
    
    relation_type = request.form.get('relation_type', 'synonym')
    min_score = float(request.form.get('min_score', 0.7))
    max_relations = int(request.form.get('max_relations', 5))
    
    try:
        result = enrich_thesaurus(wordlist, relation_type, min_score, max_relations)
        if result.returncode == 0:
            flash('Pengayaan tesaurus berhasil dilakukan', 'success')
        else:
            flash(f'Error saat melakukan pengayaan tesaurus: {result.stderr}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.admin'))











