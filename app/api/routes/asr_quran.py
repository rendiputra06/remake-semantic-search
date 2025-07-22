from flask import Blueprint, request, jsonify, render_template
import os
import datetime
from werkzeug.utils import secure_filename
from backend.db import get_db_connection, get_all_surah, get_verses_by_surah, get_asr_history, get_asr_history_detail, get_surah_by_number, get_verse_by_id
import json
import whisper
import torch

def remove_arabic_diacritics(text):
    """
    Menghapus tanda baca (harakat/tashkeel) dari teks Arab
    """
    import re
    # Pola regex untuk mencocokkan semua tanda harakat dan diacritics Arab
    arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
    return arabic_diacritics.sub('', text)

def simple_compare(ref, hyp):
    """
    Bandingkan dua string (ref, hyp) per kata, return highlight list dan skor sederhana
    """
    import re
    # Hapus diacritics dari teks referensi untuk perbandingan yang lebih akurat
    ref_clean = remove_arabic_diacritics(ref)
    # hyp sudah dibersihkan sebelumnya, tapi pastikan konsisten
    hyp_clean = remove_arabic_diacritics(hyp)
    
    ref_tokens = re.findall(r'\w+', ref_clean)
    hyp_tokens = re.findall(r'\w+', hyp_clean)
    highlight = []
    benar = 0
    for i, token in enumerate(ref_tokens):
        if i < len(hyp_tokens) and hyp_tokens[i] == token:
            highlight.append({'kata': token, 'status': 'benar'})
            benar += 1
        else:
            highlight.append({'kata': token, 'status': 'salah'})
    # Tambahan di hyp
    for j in range(len(ref_tokens), len(hyp_tokens)):
        highlight.append({'kata': hyp_tokens[j], 'status': 'tambahan'})
    skor = benar
    return highlight, skor

asr_quran_bp = Blueprint('asr_quran', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'asr_quran')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@asr_quran_bp.route('/upload', methods=['GET'])
def upload_page():
    """
    Halaman untuk upload dan uji bacaan Al Quran
    """
    return render_template('asr_quran/upload.html')

@asr_quran_bp.route('/surah', methods=['GET'])
def api_asr_get_surah():
    """
    Endpoint untuk mendapatkan daftar surah tertentu (khusus API ASR Quran)
    Hanya menampilkan surah dengan nomor 1, 107, 108, 112, 113, 114
    """
    try:
        surah_list = get_all_surah()
        # Filter hanya surah dengan nomor tertentu
        allowed_surah_numbers = [1, 107, 108, 112, 113, 114]
        filtered_surah_list = [s for s in surah_list if s['surah_number'] in allowed_surah_numbers]
        
        result = [
            {
                'id': s['id'],
                'nama_arab': s['surah_name'],
                'nama_latin': s.get('surah_name_en', ''),
                'jumlah_ayat': s['total_ayat']
            }
            for s in filtered_surah_list
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@asr_quran_bp.route('/ayat', methods=['GET'])
def api_asr_get_ayat():
    """
    Endpoint untuk mendapatkan daftar ayat dari surah tertentu (khusus API ASR Quran)
    """
    surah_id = request.args.get('surah_id')
    if not surah_id:
        return jsonify({'error': 'Parameter surah_id wajib diisi'}), 400
    try:
        ayat_list = get_verses_by_surah(int(surah_id))
        result = [
            {
                'id': a['id'],
                'nomor_ayat': a['verse_number'],
                'teks_arab': a['verse_text'],
                'teks_terjemah': a.get('verse_translation', '')
            }
            for a in ayat_list
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

@asr_quran_bp.route('/riwayat', methods=['GET'])
def api_asr_get_riwayat():
    """
    Endpoint untuk mengambil seluruh data riwayat latihan ASR Quran
    """
    try:
        rows = get_asr_history()
        result = []
        for row in rows:
            # Ambil info surah
            surah_data = get_surah_by_number(row['surah'])
            surah_nama = surah_data['surah_name'] if surah_data else ''
            ayat_data = get_verse_by_id(row['ayat'])
            # Highlight detail
            detail = []
            if row['comparison_json']:
                try:
                    detail = json.loads(row['comparison_json'])
                except Exception:
                    detail = []
            result.append({
                'id': row['history_id'],
                'nama_user': row['username'],
                'waktu': row['waktu'],
                'surah': surah_nama,
                'ayat': str(row['ayat']),
                'mode': row['mode'],
                'hasil_transkripsi': row['hyp_text'],
                'referensi_ayat': row['ref_text'],
                'skor': row['score'],
                'detail': detail
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@asr_quran_bp.route('/riwayat/<int:history_id>', methods=['GET'])
def api_asr_get_riwayat_detail(history_id):
    """
    Endpoint untuk mengambil detail riwayat latihan berdasarkan id
    """
    row = get_asr_history_detail(history_id)
    if not row:
        return jsonify({'error': 'Data riwayat tidak ditemukan'}), 404
    # Ambil info surah dan ayat
    surah_data = get_surah_by_number(row['surah'])
    ayat_data = get_verse_by_id(row['ayat'])
    # Format surah_data dan ayat_data sesuai dokumentasi
    surah_obj = None
    if surah_data:
        surah_obj = {
            'id': surah_data['id'],
            'nama_arab': surah_data['surah_name'],
            'nama_latin': surah_data.get('surah_name_en', ''),
            'jumlah_ayat': surah_data['total_ayat']
        }
    ayat_obj = None
    if ayat_data:
        ayat_obj = {
            'id': ayat_data['id'],
            'nomor_ayat': ayat_data['verse_number'],
            'teks_arab': ayat_data['verse_text'],
            'teks_terjemah': ayat_data.get('verse_translation', '')
        }
    # Highlight detail
    detail = []
    if row['comparison_json']:
        try:
            detail = json.loads(row['comparison_json'])
        except Exception:
            detail = []
    return jsonify({
        'id': row['history_id'],
        'nama_user': row['username'],
        'waktu': row['waktu'],
        'surah': surah_data['surah_name'] if surah_data else '',
        'ayat': str(row['ayat']),
        'mode': row['mode'],
        'hasil_transkripsi': row['hyp_text'],
        'referensi_ayat': row['ref_text'],
        'skor': row['score'],
        'detail': detail,
        'surah_data': surah_obj,
        'ayat_data': ayat_obj
    }) 

@asr_quran_bp.route('/riwayat/<int:history_id>', methods=['DELETE'])
def api_asr_delete_riwayat(history_id):
    """
    Endpoint untuk menghapus data riwayat latihan berdasarkan id
    """
    try:
        # Periksa apakah riwayat ada
        row = get_asr_history_detail(history_id)
        if not row:
            return jsonify({'error': 'Data riwayat tidak ditemukan'}), 404
        
        # Hapus data dari database
        conn = get_db_connection('asr_quran')
        cursor = conn.cursor()
        
        # Ambil session_id dari riwayat
        session_id = row['session_id']
        
        # Hapus dari tabel asr_history
        cursor.execute('DELETE FROM asr_history WHERE id = ?', (history_id,))
        
        # Hapus dari tabel asr_results
        cursor.execute('DELETE FROM asr_results WHERE session_id = ?', (session_id,))
        
        # Hapus dari tabel asr_sessions
        cursor.execute('DELETE FROM asr_sessions WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        # Hapus file audio jika ada
        if row['audio_path'] and os.path.exists(row['audio_path']):
            os.remove(row['audio_path'])
        
        return jsonify({'success': True, 'message': 'Data riwayat berhasil dihapus'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@asr_quran_bp.route('/asr/upload', methods=['POST'])
def api_asr_upload():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'File audio tidak ditemukan'}), 400
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'Nama file kosong'}), 400
        ayat_id = request.form.get('ayat_id')
        nama_user = request.form.get('nama_user', 'user')
        if not ayat_id:
            return jsonify({'error': 'ayat_id wajib diisi'}), 400
        # Simpan file audio
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{secure_filename(nama_user)}_{ayat_id}_{timestamp}_{secure_filename(file.filename)}"
        audio_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(audio_path)
        # Transkripsi audio
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = whisper.load_model('base', device=device)
            result = model.transcribe(audio_path, language='ar')
            transcript = remove_arabic_diacritics(result['text'].strip())
        except Exception as e:
            return jsonify({'error': f'Gagal transkripsi audio: {str(e)}'}), 500
        # Ambil ayat referensi
        ayat_data = get_verse_by_id(int(ayat_id))
        if not ayat_data:
            return jsonify({'error': 'Ayat referensi tidak ditemukan'}), 404
        ref_text = ayat_data['verse_text']
        # Bandingkan hasil transkripsi dengan referensi
        highlight, skor = simple_compare(ref_text, transcript)
        # Simpan user jika belum ada
        conn = get_db_connection('asr_quran')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM asr_users WHERE username = ?', (nama_user,))
        user_row = cursor.fetchone()
        if user_row:
            asr_user_id = user_row['id']
        else:
            cursor.execute('INSERT INTO asr_users (username, created_at) VALUES (?, ?)',
                           (nama_user, datetime.datetime.now().isoformat()))
            asr_user_id = cursor.lastrowid
        # Simpan sesi latihan
        start_time = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO asr_sessions (user_id, surah, ayat, mode, start_time, score, audio_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (asr_user_id, ayat_data['surah_id'], ayat_data['id'], 'basic', start_time, skor, audio_path))
        session_id = cursor.lastrowid
        # Simpan hasil detail perbandingan
        cursor.execute('''
            INSERT INTO asr_results (session_id, ref_text, hyp_text, comparison_json, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, ref_text, transcript, json.dumps(highlight, ensure_ascii=False), start_time))
        # Simpan riwayat
        cursor.execute('''
            INSERT INTO asr_history (user_id, session_id, score, created_at)
            VALUES (?, ?, ?, ?)
        ''', (asr_user_id, session_id, skor, start_time))
        conn.commit()
        conn.close()
        # Format ayat_data untuk response
        surah_obj = None
        from backend.db import get_surah_by_number
        surah_data = get_surah_by_number(ayat_data['surah_id'])
        if surah_data:
            surah_obj = {
                'surah_id': surah_data['id'],
                'surah': surah_data['surah_name'],
                'surah_latin': surah_data.get('surah_name_en', ''),
                'id': ayat_data['id'],
                'ayat': ayat_data['verse_number'],
                'teks': ayat_data['verse_text']
            }
        return jsonify({
            'transcript': transcript,
            'skor': skor,
            'highlight': highlight,
            'ayat_referensi': ref_text,
            'ayat_data': surah_obj
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500