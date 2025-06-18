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

def get_db_connection(db_type=None):
    """
    Mendapatkan koneksi database
    """
    if db_type == 'thesaurus':
        # Koneksi untuk database thesaurus (lexical.db)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'lexical.db')
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

if __name__ == "__main__":
    # Inisialisasi database jika dijalankan langsung
    init_db() 