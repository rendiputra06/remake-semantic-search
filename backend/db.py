"""
Modul untuk penanganan database SQLite
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Dict, Any, List, Optional, Tuple, Union
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/app.db')

def init_db():
    """
    Inisialisasi database
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buat tabel users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    ''')
    
    # Buat tabel settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        default_model TEXT NOT NULL DEFAULT 'word2vec',
        result_limit INTEGER NOT NULL DEFAULT 10,
        threshold REAL NOT NULL DEFAULT 0.5,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Buat tabel model_status
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS model_status (
        model TEXT PRIMARY KEY,
        initialized BOOLEAN NOT NULL DEFAULT 0,
        last_updated TEXT
    )
    ''')
    
    # Buat tabel search_history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        query TEXT NOT NULL,
        model TEXT NOT NULL,
        result_count INTEGER NOT NULL,
        search_time TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Buat tabel quran_index untuk menyimpan index Al-Quran
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quran_index (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        parent_id INTEGER DEFAULT NULL,
        level INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 0,
        list_ayat TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (parent_id) REFERENCES quran_index (id)
    )
    ''')
    
    # Buat tabel untuk menyimpan informasi surah Al-Quran
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quran_surah (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        surah_number INTEGER NOT NULL UNIQUE,
        surah_name TEXT NOT NULL,
        surah_name_en TEXT,
        total_ayat INTEGER NOT NULL,
        revelation_type TEXT,
        description TEXT
    )
    ''')
    
    # Buat tabel untuk menyimpan data ayat Al-Quran asli
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quran_verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        surah_id INTEGER NOT NULL,
        surah_name TEXT NOT NULL,
        verse_number INTEGER NOT NULL,
        verse_text TEXT NOT NULL,
        verse_translation TEXT,
        juz INTEGER,
        hizb INTEGER,
        ruku INTEGER,
        FOREIGN KEY (surah_id) REFERENCES quran_surah (surah_number),
        UNIQUE(surah_id, verse_number)
    )
    ''')
    
    # Buat tabel untuk semantic_index_verse (hubungan many-to-many antara index dan verse)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS semantic_index_verse (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_id INTEGER NOT NULL,
        verse_id INTEGER NOT NULL,
        score REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (index_id) REFERENCES quran_index (id),
        FOREIGN KEY (verse_id) REFERENCES quran_verses (id),
        UNIQUE(index_id, verse_id)
    )
    ''')
    
    # Buat tabel untuk statistik penggunaan aplikasi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS app_statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        total_searches INTEGER DEFAULT 0,
        unique_users INTEGER DEFAULT 0,
        popular_model TEXT,
        avg_result_count REAL DEFAULT 0
    )
    ''')
    
    # Buat tabel queries untuk evaluasi benchmark
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Buat tabel relevant_verses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relevant_verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER NOT NULL,
        verse_ref TEXT NOT NULL,
        FOREIGN KEY (query_id) REFERENCES queries (id)
    )
    ''')
    
    # Buat tabel evaluation_results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluation_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER NOT NULL,
        model TEXT NOT NULL,
        precision REAL,
        recall REAL,
        f1 REAL,
        exec_time REAL,
        evaluated_at TEXT NOT NULL,
        FOREIGN KEY (query_id) REFERENCES queries (id)
    )
    ''')
    
    # Buat tabel evaluation_log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id INTEGER NOT NULL,
        model TEXT NOT NULL,
        old_score REAL,
        new_score REAL,
        changed_at TEXT NOT NULL,
        FOREIGN KEY (query_id) REFERENCES queries (id)
    )
    ''')
    
    # Buat tabel global_model_settings untuk threshold per model (global)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS global_model_settings (
        model TEXT PRIMARY KEY,
        threshold REAL NOT NULL
    )
    ''')
    # Inisialisasi default threshold jika belum ada
    default_models = [
        ('word2vec', 0.5),
        ('fasttext', 0.5),
        ('glove', 0.5),
        ('ensemble', 0.5),
        ('ontology', 0.5)
    ]
    for model, threshold in default_models:
        cursor.execute('INSERT OR IGNORE INTO global_model_settings (model, threshold) VALUES (?, ?)', (model, threshold))
    
    # Inisialisasi data awal untuk model_status
    models = ['word2vec', 'fasttext', 'glove', 'lexical', 'thesaurus']
    for model in models:
        cursor.execute('''
        INSERT OR IGNORE INTO model_status (model, initialized, last_updated)
        VALUES (?, 0, NULL)
        ''', (model,))
    
    # Tambahkan admin jika belum ada
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        now = datetime.datetime.now().isoformat()
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
        INSERT INTO users (username, password, email, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'admin@example.com', 'admin', now))
        
        # Dapatkan ID admin yang baru dibuat
        admin_id = cursor.lastrowid
        
        # Tambahkan pengaturan untuk admin
        cursor.execute('''
        INSERT INTO settings (user_id, default_model, result_limit, threshold)
        VALUES (?, ?, ?, ?)
        ''', (admin_id, 'word2vec', 10, 0.5))
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

def init_asr_quran_db():
    """
    Inisialisasi database ASR Quran (asr_quran.db) dan tabel-tabel utama
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'asr_quran.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tabel user latihan (jika ingin tracking user, bisa dihubungkan ke user utama via user_id)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asr_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        user_id INTEGER,
        created_at TEXT NOT NULL
    )
    ''')

    # Tabel latihan ASR Quran
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asr_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        surah INTEGER,
        ayat INTEGER,
        mode TEXT NOT NULL, -- basic/lanjutan
        start_time TEXT NOT NULL,
        end_time TEXT,
        score REAL,
        audio_path TEXT,
        FOREIGN KEY (user_id) REFERENCES asr_users(id)
    )
    ''')

    # Tabel hasil detail perbandingan (per ayat, per token, dsb)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asr_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        ref_text TEXT NOT NULL,
        hyp_text TEXT NOT NULL,
        comparison_json TEXT, -- JSON detail highlight benar/salah/tambahan
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES asr_sessions(id)
    )
    ''')

    # Tabel riwayat latihan (untuk query cepat)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS asr_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_id INTEGER,
        score REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES asr_users(id),
        FOREIGN KEY (session_id) REFERENCES asr_sessions(id)
    )
    ''')

    conn.commit()
    conn.close()

def get_db_connection(db_type=None):
    """
    Mendapatkan koneksi database
    """
    if db_type == 'thesaurus':
        # Koneksi untuk database thesaurus (lexical.db)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'lexical.db')
    elif db_type == 'asr_quran':
        # Koneksi untuk database ASR Quran (asr_quran.db)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'asr_quran.db')
    else:
        # Koneksi untuk database utama (app.db)
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Mendapatkan user berdasarkan username
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Mendapatkan user berdasarkan ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return dict(user)
    return None

def register_user(username: str, password: str, email: str) -> Tuple[bool, str]:
    """
    Mendaftarkan user baru
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Cek apakah username atau email sudah terdaftar
        cursor.execute('SELECT username FROM users WHERE username = ? OR email = ?', 
                      (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return False, "Username atau email sudah terdaftar."
        
        # Tambahkan user baru
        hashed_password = generate_password_hash(password)
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO users (username, password, email, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, hashed_password, email, 'user', now))
        
        # Tambahkan pengaturan default untuk user baru
        user_id = cursor.lastrowid
        cursor.execute('''
        INSERT INTO settings (user_id, default_model, result_limit, threshold)
        VALUES (?, ?, ?, ?)
        ''', (user_id, 'word2vec', 10, 0.5))
        
        conn.commit()
        conn.close()
        return True, "Pendaftaran berhasil."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat mendaftarkan user: {str(e)}"

def authenticate_user(username: str, password: str) -> Tuple[bool, Union[int, str]]:
    """
    Autentikasi user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Dapatkan user
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            # Update last_login
            now = datetime.datetime.now().isoformat()
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (now, user['id']))
            conn.commit()
            
            conn.close()
            return True, user['id']
        else:
            conn.close()
            return False, "Username atau password salah."
    except Exception as e:
        conn.close()
        return False, f"Error saat autentikasi: {str(e)}"

def get_user_settings(user_id: int) -> Dict[str, Any]:
    """
    Mendapatkan pengaturan user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM settings WHERE user_id = ?', (user_id,))
    settings = cursor.fetchone()
    
    conn.close()
    
    if settings:
        return dict(settings)
    else:
        # Default settings jika belum ada
        return {
            'user_id': user_id,
            'default_model': 'word2vec',
            'result_limit': 10,
            'threshold': 0.5
        }

def update_user_settings(user_id: int, default_model: str, result_limit: int, threshold: float) -> Tuple[bool, str]:
    """
    Memperbarui pengaturan user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Validasi input
        if result_limit < 0:
            return False, "Jumlah hasil tidak boleh negatif"
        
        if threshold < 0 or threshold > 1:
            return False, "Threshold harus antara 0 dan 1"
        
        cursor.execute('''
        UPDATE settings 
        SET default_model = ?, result_limit = ?, threshold = ?
        WHERE user_id = ?
        ''', (default_model, result_limit, threshold, user_id))
        
        if cursor.rowcount == 0:
            # Insert if not exists
            cursor.execute('''
            INSERT INTO settings (user_id, default_model, result_limit, threshold)
            VALUES (?, ?, ?, ?)
            ''', (user_id, default_model, result_limit, threshold))
        
        conn.commit()
        conn.close()
        return True, "Pengaturan berhasil diperbarui."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat memperbarui pengaturan: {str(e)}"

def add_search_history(user_id: int, query: str, model: str, result_count: int) -> bool:
    """
    Menambahkan histori pencarian
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO search_history (user_id, query, model, result_count, search_time)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, query, model, result_count, now))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saat menambahkan histori pencarian: {str(e)}")
        return False

def get_search_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Mendapatkan histori pencarian user
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM search_history 
    WHERE user_id = ? 
    ORDER BY search_time DESC 
    LIMIT ?
    ''', (user_id, limit))
    
    history = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in history]

def get_model_status() -> Dict[str, Dict[str, Any]]:
    """
    Mendapatkan status semua model
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM model_status')
    models = cursor.fetchall()
    
    conn.close()
    
    status = {}
    for model in models:
        status[model['model']] = {
            'initialized': bool(model['initialized']),
            'last_updated': model['last_updated']
        }
    
    return status

def update_model_status(model_name: str, initialized: bool) -> bool:
    """
    Memperbarui status model
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.datetime.now().isoformat()
        cursor.execute('''
        UPDATE model_status 
        SET initialized = ?, last_updated = ?
        WHERE model = ?
        ''', (1 if initialized else 0, now, model_name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saat memperbarui status model: {str(e)}")
        return False

# Fungsi-fungsi untuk mengelola quran_index dan quran_ayat

def get_quran_indexes(parent_id=None):
    """
    Mendapatkan daftar index Al-Quran berdasarkan parent_id
    Jika parent_id None, ambil semua index level teratas (root)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if parent_id is None:
        # Ambil index level teratas
        cursor.execute('''
        SELECT * FROM quran_index 
        WHERE parent_id IS NULL 
        ORDER BY sort_order, id
        ''')
    else:
        # Ambil index berdasarkan parent_id
        cursor.execute('''
        SELECT * FROM quran_index 
        WHERE parent_id = ? 
        ORDER BY sort_order, id
        ''', (parent_id,))
    
    indexes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return indexes

def get_quran_index_by_id(index_id):
    """
    Mendapatkan detail index Al-Quran berdasarkan ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quran_index WHERE id = ?', (index_id,))
    index = cursor.fetchone()
    
    conn.close()
    
    if index:
        return dict(index)
    return None

def get_quran_ayat_by_index(index_id):
    """
    Mendapatkan ayat-ayat Al-Quran berdasarkan index_id dari kolom list_ayat
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT list_ayat FROM quran_index WHERE id = ?', (index_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result['list_ayat']:
        return []
    
    try:
        import json
        ayat_list = json.loads(result['list_ayat'])
        
        # Format ayat_list diharapkan dalam format "surah:ayat"
        # Kembalikan dalam format yang konsisten dengan API
        formatted_ayat = []
        for ayat_ref in ayat_list:
            parts = ayat_ref.split(':')
            if len(parts) == 2:
                surah, ayat = parts
                formatted_ayat.append({
                    'surah': int(surah),
                    'ayat': int(ayat),
                    'ayat_ref': ayat_ref
                })
        
        return formatted_ayat
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing list_ayat: {e}")
        return []

def get_quran_ayat_detail_by_index(index_id):
    """
    Mendapatkan ayat-ayat Al-Quran lengkap dengan teks dan terjemahan berdasarkan index_id
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT list_ayat FROM quran_index WHERE id = ?', (index_id,))
    result = cursor.fetchone()
    
    if not result or not result['list_ayat']:
        conn.close()
        return []
    
    try:
        import json
        ayat_list = json.loads(result['list_ayat'])
        
        # Ambil detail ayat dari database
        detailed_ayat = []
        for ayat_ref in ayat_list:
            parts = ayat_ref.split(':')
            if len(parts) == 2:
                surah_num, ayat_num = int(parts[0]), int(parts[1])
                
                # Ambil data ayat dari tabel quran_verses
                cursor.execute('''
                    SELECT v.*, s.surah_name_en 
                    FROM quran_verses v 
                    JOIN quran_surah s ON v.surah_id = s.surah_number 
                    WHERE v.surah_id = ? AND v.verse_number = ?
                ''', (surah_num, ayat_num))
                
                verse_data = cursor.fetchone()
                if verse_data:
                    detailed_ayat.append({
                        'id': verse_data['id'],
                        'surah': surah_num,
                        'surah_name': verse_data['surah_name'],
                        'surah_name_en': verse_data['surah_name_en'],
                        'ayat': ayat_num,
                        'text': verse_data['verse_text'],
                        'translation': verse_data['verse_translation'],
                        'ayat_ref': ayat_ref
                    })
        
        conn.close()
        return detailed_ayat
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing list_ayat: {e}")
        conn.close()
        return []

def add_quran_index(title, description=None, parent_id=None, level=1, sort_order=0):
    """
    Menambahkan index Al-Quran baru
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute('''
        INSERT INTO quran_index (title, description, parent_id, level, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, parent_id, level, sort_order, now, now))
        
        index_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, index_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_quran_index(index_id, title, description=None, parent_id=None, level=1, sort_order=0):
    """
    Memperbarui index Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute('''
        UPDATE quran_index 
        SET title = ?, description = ?, parent_id = ?, level = ?, sort_order = ?, updated_at = ?
        WHERE id = ?
        ''', (title, description, parent_id, level, sort_order, now, index_id))
        
        conn.commit()
        conn.close()
        
        return True, "Index berhasil diperbarui"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def delete_quran_index(index_id):
    """
    Menghapus index Al-Quran
    Catatan: Operasi ini akan menghapus semua sub-index
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ambil semua sub-index untuk dihapus secara rekursif
        cursor.execute('SELECT id FROM quran_index WHERE parent_id = ?', (index_id,))
        sub_indexes = cursor.fetchall()
        
        # Hapus sub-index secara rekursif
        for sub_index in sub_indexes:
            delete_quran_index(sub_index['id'])
        
        # Hapus hubungan dengan verses di tabel semantic_index_verse jika ada
        cursor.execute('DELETE FROM semantic_index_verse WHERE index_id = ?', (index_id,))
        
        # Hapus index itu sendiri
        cursor.execute('DELETE FROM quran_index WHERE id = ?', (index_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Index berhasil dihapus"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

def update_quran_index_ayat(index_id, ayat_list):
    """
    Memperbarui daftar ayat (list_ayat) pada index Al-Quran
    
    Args:
        index_id (int): ID index
        ayat_list (list): Daftar referensi ayat dalam format ["surah:ayat", ...]
        
    Returns:
        tuple: (success, message)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.datetime.now().isoformat()
    
    try:
        # Validasi format ayat_list
        import json
        for ayat_ref in ayat_list:
            parts = ayat_ref.split(':')
            if len(parts) != 2:
                return False, f"Format referensi ayat tidak valid: {ayat_ref}. Gunakan format 'surah:ayat'"
            
            # Pastikan bisa dikonversi ke integer
            try:
                int(parts[0]), int(parts[1])
            except ValueError:
                return False, f"Nomor surah dan ayat harus berupa angka: {ayat_ref}"
        
        # Konversi ke JSON string
        ayat_json = json.dumps(ayat_list)
        
        # Update kolom list_ayat
        cursor.execute('''
        UPDATE quran_index 
        SET list_ayat = ?, updated_at = ?
        WHERE id = ?
        ''', (ayat_json, now, index_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True, "Daftar ayat berhasil diperbarui"
        else:
            conn.close()
            return False, "Index tidak ditemukan"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Fungsi-fungsi untuk mengelola tabel quran_surah

def get_all_surah():
    """
    Mendapatkan daftar semua surah Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quran_surah ORDER BY surah_number')
    surah_list = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in surah_list]

def get_surah_by_number(surah_number):
    """
    Mendapatkan informasi surah berdasarkan nomor surah
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quran_surah WHERE surah_number = ?', (surah_number,))
    surah = cursor.fetchone()
    
    conn.close()
    
    if surah:
        return dict(surah)
    return None

def add_surah(surah_number, surah_name, total_ayat, surah_name_en=None, revelation_type=None, description=None):
    """
    Menambahkan data surah Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO quran_surah (
            surah_number, 
            surah_name, 
            surah_name_en, 
            total_ayat, 
            revelation_type, 
            description
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (surah_number, surah_name, surah_name_en, total_ayat, revelation_type, description))
        
        surah_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, surah_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan surah: {str(e)}"

def update_surah(surah_number, surah_name=None, total_ayat=None, surah_name_en=None, revelation_type=None, description=None):
    """
    Memperbarui data surah Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Dapatkan data surah yang akan diupdate
        cursor.execute('SELECT * FROM quran_surah WHERE surah_number = ?', (surah_number,))
        existing_surah = cursor.fetchone()
        
        if not existing_surah:
            conn.close()
            return False, "Surah tidak ditemukan."
        
        # Persiapkan data yang akan diupdate
        update_data = dict(existing_surah)
        
        if surah_name is not None:
            update_data['surah_name'] = surah_name
        if total_ayat is not None:
            update_data['total_ayat'] = total_ayat
        if surah_name_en is not None:
            update_data['surah_name_en'] = surah_name_en
        if revelation_type is not None:
            update_data['revelation_type'] = revelation_type
        if description is not None:
            update_data['description'] = description
        
        # Update data
        cursor.execute('''
        UPDATE quran_surah 
        SET 
            surah_name = ?, 
            surah_name_en = ?, 
            total_ayat = ?, 
            revelation_type = ?, 
            description = ?
        WHERE surah_number = ?
        ''', (
            update_data['surah_name'], 
            update_data['surah_name_en'], 
            update_data['total_ayat'], 
            update_data['revelation_type'], 
            update_data['description'], 
            surah_number
        ))
        
        conn.commit()
        conn.close()
        return True, "Data surah berhasil diperbarui."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat memperbarui surah: {str(e)}"

# Fungsi-fungsi untuk mengelola tabel quran_verses

def get_verse_by_id(verse_id):
    """
    Mendapatkan ayat Al-Quran berdasarkan ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quran_verses WHERE id = ?', (verse_id,))
    verse = cursor.fetchone()
    
    conn.close()
    
    if verse:
        return dict(verse)
    return None

def get_verses_by_surah(surah_id):
    """
    Mendapatkan semua ayat dari surah tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM quran_verses WHERE surah_id = ? ORDER BY verse_number', (surah_id,))
    verses = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in verses]

def add_verse(surah_id, surah_name, verse_number, verse_text, verse_translation=None, juz=None, hizb=None, ruku=None):
    """
    Menambahkan ayat Al-Quran ke database
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO quran_verses (
            surah_id, 
            surah_name, 
            verse_number, 
            verse_text, 
            verse_translation, 
            juz, 
            hizb, 
            ruku
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (surah_id, surah_name, verse_number, verse_text, verse_translation, juz, hizb, ruku))
        
        verse_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, verse_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan ayat: {str(e)}"

def update_verse(verse_id, verse_text=None, verse_translation=None, juz=None, hizb=None, ruku=None):
    """
    Memperbarui data ayat Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Dapatkan data ayat yang akan diupdate
        cursor.execute('SELECT * FROM quran_verses WHERE id = ?', (verse_id,))
        existing_verse = cursor.fetchone()
        
        if not existing_verse:
            conn.close()
            return False, "Ayat tidak ditemukan."
        
        # Persiapkan data yang akan diupdate
        update_data = dict(existing_verse)
        
        if verse_text is not None:
            update_data['verse_text'] = verse_text
        if verse_translation is not None:
            update_data['verse_translation'] = verse_translation
        if juz is not None:
            update_data['juz'] = juz
        if hizb is not None:
            update_data['hizb'] = hizb
        if ruku is not None:
            update_data['ruku'] = ruku
        
        # Update data
        cursor.execute('''
        UPDATE quran_verses 
        SET 
            verse_text = ?, 
            verse_translation = ?, 
            juz = ?, 
            hizb = ?, 
            ruku = ?
        WHERE id = ?
        ''', (
            update_data['verse_text'], 
            update_data['verse_translation'], 
            update_data['juz'], 
            update_data['hizb'], 
            update_data['ruku'], 
            verse_id
        ))
        
        conn.commit()
        conn.close()
        return True, "Data ayat berhasil diperbarui."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat memperbarui ayat: {str(e)}"

# Fungsi-fungsi untuk mengelola tabel semantic_index_verse

def link_index_to_verse(index_id, verse_id, score=None):
    """
    Menghubungkan index dengan ayat Al-Quran
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO semantic_index_verse (
            index_id,
            verse_id,
            score,
            created_at
        )
        VALUES (?, ?, ?, ?)
        ''', (index_id, verse_id, score, now))
        
        link_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, link_id
    except sqlite3.IntegrityError:
        # Jika sudah ada hubungan, update score saja
        if score is not None:
            cursor.execute('''
            UPDATE semantic_index_verse
            SET score = ?
            WHERE index_id = ? AND verse_id = ?
            ''', (score, index_id, verse_id))
            
            conn.commit()
            conn.close()
            return True, "Hubungan diperbarui."
        else:
            conn.close()
            return False, "Hubungan antara index dan ayat sudah ada."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menghubungkan index dengan ayat: {str(e)}"

def get_verses_by_index(index_id):
    """
    Mendapatkan semua ayat yang terkait dengan index tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT v.*, s.score
    FROM quran_verses v
    JOIN semantic_index_verse s ON v.id = s.verse_id
    WHERE s.index_id = ?
    ORDER BY s.score DESC
    ''', (index_id,))
    
    verses = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in verses]

def get_indexes_by_verse(verse_id):
    """
    Mendapatkan semua index yang terkait dengan ayat tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT i.*, s.score
    FROM quran_index i
    JOIN semantic_index_verse s ON i.id = s.index_id
    WHERE s.verse_id = ?
    ORDER BY s.score DESC
    ''', (verse_id,))
    
    indexes = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in indexes]

# Fungsi-fungsi untuk mengelola tabel app_statistics

def update_app_statistics(date=None, searches=0, users=0, model=None, avg_results=0):
    """
    Memperbarui statistik penggunaan aplikasi
    """
    if date is None:
        date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Cek apakah sudah ada statistik untuk tanggal ini
        cursor.execute('SELECT * FROM app_statistics WHERE date = ?', (date,))
        existing_stats = cursor.fetchone()
        
        if existing_stats:
            # Update statistik yang sudah ada
            stats = dict(existing_stats)
            
            if model is not None:
                # Hitung model yang paling populer
                cursor.execute('''
                SELECT model, COUNT(*) as count 
                FROM search_history 
                WHERE date(search_time) = ? 
                GROUP BY model 
                ORDER BY count DESC 
                LIMIT 1
                ''', (date,))
                most_popular = cursor.fetchone()
                if most_popular:
                    stats['popular_model'] = most_popular['model']
            
            # Update statistik
            cursor.execute('''
            UPDATE app_statistics
            SET 
                total_searches = total_searches + ?,
                unique_users = ?,
                popular_model = ?,
                avg_result_count = ?
            WHERE date = ?
            ''', (
                searches,
                stats['unique_users'] + users,
                stats['popular_model'] if model is None else model,
                (stats['avg_result_count'] * stats['total_searches'] + avg_results * searches) / (stats['total_searches'] + searches) if searches > 0 else stats['avg_result_count'],
                date
            ))
        else:
            # Buat statistik baru
            cursor.execute('''
            INSERT INTO app_statistics (
                date,
                total_searches,
                unique_users,
                popular_model,
                avg_result_count
            )
            VALUES (?, ?, ?, ?, ?)
            ''', (date, searches, users, model, avg_results))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saat memperbarui statistik: {str(e)}")
        return False

def get_app_statistics(start_date=None, end_date=None):
    """
    Mendapatkan statistik penggunaan aplikasi dalam rentang waktu tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if start_date is None and end_date is None:
        # Ambil 30 hari terakhir
        cursor.execute('''
        SELECT * FROM app_statistics
        ORDER BY date DESC
        LIMIT 30
        ''')
    elif start_date is not None and end_date is None:
        # Ambil statistik dari tanggal mulai
        cursor.execute('''
        SELECT * FROM app_statistics
        WHERE date >= ?
        ORDER BY date
        ''', (start_date,))
    elif start_date is None and end_date is not None:
        # Ambil statistik sampai tanggal akhir
        cursor.execute('''
        SELECT * FROM app_statistics
        WHERE date <= ?
        ORDER BY date
        ''', (end_date,))
    else:
        # Ambil statistik dalam rentang waktu
        cursor.execute('''
        SELECT * FROM app_statistics
        WHERE date BETWEEN ? AND ?
        ORDER BY date
        ''', (start_date, end_date))
    
    stats = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in stats]

def get_overall_statistics():
    """
    Mendapatkan statistik keseluruhan aplikasi
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total pencarian
    cursor.execute('SELECT COUNT(*) as total FROM search_history')
    total_searches = cursor.fetchone()['total']
    
    # Total pengguna aktif
    cursor.execute('SELECT COUNT(DISTINCT user_id) as total FROM search_history')
    total_users = cursor.fetchone()['total']
    
    # Model terpopuler
    cursor.execute('''
    SELECT model, COUNT(*) as count 
    FROM search_history 
    GROUP BY model 
    ORDER BY count DESC 
    LIMIT 1
    ''')
    most_popular_model = cursor.fetchone()
    popular_model = most_popular_model['model'] if most_popular_model else None
    
    # Rata-rata hasil pencarian
    cursor.execute('SELECT AVG(result_count) as avg FROM search_history')
    avg_results = cursor.fetchone()['avg']
    
    conn.close()
    
    return {
        'total_searches': total_searches,
        'total_users': total_users,
        'popular_model': popular_model,
        'avg_results': avg_results
    }

def add_query(text: str):
    """
    Menambahkan query evaluasi ke tabel queries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute('''
        INSERT INTO queries (text, created_at)
        VALUES (?, ?)
        ''', (text, now))
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, query_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan query: {str(e)}"

def get_all_queries():
    """
    Mengambil semua query evaluasi dari tabel queries
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM queries ORDER BY created_at DESC')
    queries = cursor.fetchall()
    conn.close()
    return [dict(row) for row in queries]

def add_relevant_verse(query_id: int, verse_ref: str):
    """
    Menambahkan ayat relevan untuk query tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO relevant_verses (query_id, verse_ref)
        VALUES (?, ?)
        ''', (query_id, verse_ref))
        rel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, rel_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan relevant verse: {str(e)}"

def add_relevant_verses_batch(query_id: int, ayat_list: list):
    """
    Enhanced batch insert dengan deduplication dan detailed feedback.
    Menambahkan banyak ayat relevan untuk query tertentu secara batch (lebih cepat).
    Sekarang dengan existing verse checking dan detailed statistics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get existing verses for this query untuk deduplication
        cursor.execute('SELECT verse_ref FROM relevant_verses WHERE query_id = ?', (query_id,))
        existing_verses = {row['verse_ref'] for row in cursor.fetchall()}

        # Filter out duplicates dan hitung statistik
        new_verses = []
        duplicates_found = 0

        for verse_ref in ayat_list:
            if verse_ref in existing_verses:
                duplicates_found += 1
            else:
                new_verses.append(verse_ref)
                existing_verses.add(verse_ref)  # Add to set untuk mencegah duplikasi dalam list yang sama

        # Insert only new verses
        if new_verses:
            data = [(query_id, verse_ref) for verse_ref in new_verses]
            cursor.executemany('''
                INSERT INTO relevant_verses (query_id, verse_ref)
                VALUES (?, ?)
            ''', data)

        conn.commit()
        conn.close()

        return True, {
            'inserted': len(new_verses),
            'duplicates': duplicates_found,
            'total_processed': len(ayat_list),
            'existing_before': len(existing_verses) - len(new_verses)
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error batch insert relevant verses: {str(e)}"

def get_relevant_verses_by_query(query_id: int):
    """
    Mengambil semua ayat relevan untuk query tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM relevant_verses WHERE query_id = ?', (query_id,))
    verses = cursor.fetchall()
    conn.close()
    return [dict(row) for row in verses]

def add_evaluation_result(query_id: int, model: str, precision: float, recall: float, f1: float, exec_time: float):
    """
    Menambahkan hasil evaluasi untuk query dan model tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute('''
        INSERT INTO evaluation_results (query_id, model, precision, recall, f1, exec_time, evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (query_id, model, precision, recall, f1, exec_time, now))
        eval_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, eval_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan evaluation result: {str(e)}"

def get_evaluation_results_by_query(query_id: int):
    """
    Mengambil semua hasil evaluasi untuk query tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_results WHERE query_id = ?', (query_id,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_evaluation_log(query_id: int, model: str, old_score: float, new_score: float):
    """
    Menambahkan log perubahan skor evaluasi
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute('''
        INSERT INTO evaluation_log (query_id, model, old_score, new_score, changed_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (query_id, model, old_score, new_score, now))
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, log_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menambahkan evaluation log: {str(e)}"

def get_evaluation_logs_by_query(query_id: int):
    """
    Mengambil semua log perubahan evaluasi untuk query tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_log WHERE query_id = ?', (query_id,))
    logs = cursor.fetchall()
    conn.close()
    return [dict(row) for row in logs]

def delete_query(query_id: int):
    """
    Menghapus query evaluasi beserta ayat relevan dan hasil evaluasinya
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Hapus dalam urutan yang benar (foreign key constraints)
        cursor.execute('DELETE FROM evaluation_log WHERE query_id = ?', (query_id,))
        cursor.execute('DELETE FROM evaluation_results WHERE query_id = ?', (query_id,))
        cursor.execute('DELETE FROM relevant_verses WHERE query_id = ?', (query_id,))
        cursor.execute('DELETE FROM queries WHERE id = ?', (query_id,))
        conn.commit()
        conn.close()
        print(f"Query {query_id} dan semua data terkait berhasil dihapus.")
        return True, "Query berhasil dihapus"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menghapus query: {str(e)}"

def delete_relevant_verse(verse_id: int):
    """
    Menghapus ayat relevan berdasarkan ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM relevant_verses WHERE id = ?', (verse_id,))
        conn.commit()
        conn.close()
        return True, "Ayat relevan berhasil dihapus"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menghapus ayat relevan: {str(e)}"

def reset_relevant_verses(query_id: int):
    """
    Menghapus semua ayat relevan untuk query tertentu
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM relevant_verses WHERE query_id = ?', (query_id,))
        conn.commit()
        conn.close()
        return True, "Semua ayat relevan berhasil dihapus"
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error saat menghapus ayat relevan: {str(e)}"

def get_global_thresholds() -> dict:
    """
    Mengambil threshold semua model dari global_model_settings
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT model, threshold FROM global_model_settings')
    rows = cursor.fetchall()
    conn.close()
    return {row['model']: row['threshold'] for row in rows}

def update_global_thresholds(thresholds: dict) -> bool:
    """
    Update threshold semua model di global_model_settings
    thresholds: dict {model: threshold}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for model, threshold in thresholds.items():
            if threshold < 0 or threshold > 1:
                raise ValueError(f"Threshold untuk {model} harus antara 0 dan 1")
            cursor.execute('UPDATE global_model_settings SET threshold = ? WHERE model = ?', (threshold, model))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error update_global_thresholds: {e}")
        return False

def get_asr_history():
    """
    Mengambil seluruh data riwayat latihan ASR Quran (join asr_history, asr_sessions, asr_users, asr_results)
    """
    conn = get_db_connection('asr_quran')
    cursor = conn.cursor()
    query = '''
        SELECT h.id as history_id, u.username, h.created_at as waktu, s.surah, s.ayat, s.mode, s.score, s.id as session_id,
               r.hyp_text, r.ref_text, r.comparison_json
        FROM asr_history h
        JOIN asr_users u ON h.user_id = u.id
        JOIN asr_sessions s ON h.session_id = s.id
        LEFT JOIN asr_results r ON r.session_id = s.id
        ORDER BY h.created_at DESC
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_asr_history_detail(history_id):
    """
    Mengambil detail riwayat latihan berdasarkan id (join surah, ayat, hasil, user, highlight)
    """
    conn = get_db_connection('asr_quran')
    cursor = conn.cursor()
    query = '''
        SELECT h.id as history_id, u.username, h.created_at as waktu, s.surah, s.ayat, s.mode, s.score, s.id as session_id,
               r.hyp_text, r.ref_text, r.comparison_json,
               s.audio_path
        FROM asr_history h
        JOIN asr_users u ON h.user_id = u.id
        JOIN asr_sessions s ON h.session_id = s.id
        LEFT JOIN asr_results r ON r.session_id = s.id
        WHERE h.id = ?
        LIMIT 1
    '''
    cursor.execute(query, (history_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

if __name__ == "__main__":
    # Inisialisasi database jika dijalankan langsung
    init_db()