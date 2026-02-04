"""
Admin routes for the application.
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from backend.db import get_db_connection, add_custom_evaluation, get_all_custom_evaluations, delete_custom_evaluation, update_custom_evaluation, ensure_query_exists
from app.auth.decorators import admin_required
import pandas as pd
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












@admin_bp.route('/custom_eval')
@admin_required
def custom_eval_page():
    """Admin page for Custom Evaluation management."""
    custom_evals = get_all_custom_evaluations()
    return render_template('admin_custom_eval.html', custom_evals=custom_evals)

@admin_bp.route('/custom_eval/upload', methods=['POST'])
@admin_required
def upload_custom_eval():
    """Handle CSV upload for Custom Evaluation."""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin.custom_eval_page'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('admin.custom_eval_page'))
    
    if file:
        try:
            # Read CSV
            df = pd.read_csv(file)
            
            # Expected columns
            required_columns = ['Topic', 'W2V_Threshold', 'FT_Threshold', 'GV_Threshold', 
                              'Precision', 'Recall', 'F1_Score', 'TP', 'FP', 'FN']
            
            # Validation
            if not all(col in df.columns for col in required_columns):
                flash(f'Format CSV salah. Harus memuat kolom: {", ".join(required_columns)}', 'danger')
                return redirect(url_for('admin.custom_eval_page'))
            
            success_count = 0
            for _, row in df.iterrows():
                topic = row['Topic']
                # Sync with queries table
                ensure_query_exists(topic)
                
                data = {
                    'topic': topic,
                    'w2v_threshold': float(row['W2V_Threshold']),
                    'ft_threshold': float(row['FT_Threshold']),
                    'gv_threshold': float(row['GV_Threshold']),
                    'precision': float(row['Precision']),
                    'recall': float(row['Recall']),
                    'f1_score': float(row['F1_Score']),
                    'tp': int(row['TP']),
                    'fp': int(row['FP']),
                    'fn': int(row['FN'])
                }
                success, msg = add_custom_evaluation(data)
                if success:
                    success_count += 1
            
            flash(f'Berhasil memproses {success_count} baris data.', 'success')
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            
    return redirect(url_for('admin.custom_eval_page'))

@admin_bp.route('/custom_eval/update', methods=['POST'])
@admin_required
def update_custom_eval_route():
    """Update an existing custom evaluation entry."""
    eval_id = request.form.get('id')
    if not eval_id:
        flash('ID tidak ditemukan', 'danger')
        return redirect(url_for('admin.custom_eval_page'))
    
    data = {
        'precision': float(request.form.get('precision', 0.0)),
        'recall': float(request.form.get('recall', 0.0)),
        'f1_score': float(request.form.get('f1_score', 0.0)),
        'tp': int(request.form.get('tp', 0)),
        'fp': int(request.form.get('fp', 0)),
        'fn': int(request.form.get('fn', 0))
    }
    
    success, msg = update_custom_evaluation(int(eval_id), data)
    if success:
        flash('Data berhasil diperbarui.', 'success')
    else:
        flash(f'Gagal memperbarui: {msg}', 'danger')
        
    return redirect(url_for('admin.custom_eval_page'))

@admin_bp.route('/custom_eval/delete', methods=['POST'])
@admin_required
def delete_custom_eval():
    """Delete a custom evaluation entry by ID."""
    eval_id = request.form.get('id')
    if eval_id:
        success, msg = delete_custom_evaluation(int(eval_id))
        if success:
            flash('Data kustom evaluasi berhasil dihapus.', 'success')
        else:
            flash(f'Gagal menghapus: {msg}', 'danger')
    else:
        flash('ID tidak ditemukan', 'danger')
    return redirect(url_for('admin.custom_eval_page'))
@admin_bp.route('/api/custom_eval/batch_save', methods=['POST'])
@admin_required
def batch_save_custom_eval():
    """Batch save CSV data after preview review."""
    req = request.json
    if not req or 'data' not in req:
        return jsonify({'success': False, 'message': 'Data tidak ditemukan'}), 400
    
    rows = req['data']
    success_count = 0
    errors = []
    
    for row in rows:
        try:
            topic = row.get('Topic') or row.get('topic')
            if not topic: continue
            
            # Sync with queries table
            ensure_query_exists(topic)
            
            data = {
                'topic': topic,
                'w2v_threshold': float(row.get('W2V_Threshold') or row.get('w2v_threshold', 0.5)),
                'ft_threshold': float(row.get('FT_Threshold') or row.get('ft_threshold', 0.5)),
                'gv_threshold': float(row.get('GV_Threshold') or row.get('gv_threshold', 0.5)),
                'precision': float(row.get('Precision') or row.get('precision', 0.0)),
                'recall': float(row.get('Recall') or row.get('recall', 0.0)),
                'f1_score': float(row.get('F1_Score') or row.get('f1_score', 0.0)),
                'tp': int(row.get('TP') or row.get('tp', 0)),
                'fp': int(row.get('FP') or row.get('fp', 0)),
                'fn': int(row.get('FN') or row.get('fn', 0))
            }
            success, msg = add_custom_evaluation(data)
            if success:
                success_count += 1
            else:
                errors.append(f"{topic}: {msg}")
        except Exception as e:
            errors.append(f"Error: {str(e)}")
            
    return jsonify({
        'success': True,
        'message': f'Berhasil menyimpan {success_count} data.',
        'errors': errors
    })
