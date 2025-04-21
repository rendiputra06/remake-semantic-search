"""
Modul untuk penanganan API mesin pencarian semantik Al-Quran
"""
from flask import Blueprint, request, jsonify, session
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
from backend.db import get_user_settings, add_search_history, get_user_by_id, get_search_history, get_quran_indexes, get_quran_index_by_id, get_quran_ayat_by_index, add_quran_index, update_quran_index, delete_quran_index, get_db_connection
import os
import sys
import traceback
import datetime
import pandas as pd
import json

# Inisialisasi Blueprint untuk API
api_bp = Blueprint('api', __name__)

# Model global
word2vec_model = None
fasttext_model = None
glove_model = None

def init_model(model_type='word2vec'):
    """
    Inisialisasi model yang dipilih
    
    Args:
        model_type: Tipe model ('word2vec', 'fasttext', atau 'glove')
    """
    global word2vec_model, fasttext_model, glove_model
    
    if model_type == 'word2vec':
        if word2vec_model is None:
            try:
                # Gunakan path yang relatif terhadap root project
                model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/idwiki_word2vec/idwiki_word2vec_200_new_lower.model')
                word2vec_model = Word2VecModel(model_path=model_path)
                
                # Cek apakah file vektor ayat sudah ada
                vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/word2vec_verses.pkl')
                
                if os.path.exists(vectors_path):
                    # Muat model dan vektor ayat yang sudah ada
                    word2vec_model.load_model()
                    word2vec_model.load_verse_vectors(vectors_path)
                    print(f"Word2Vec model and verse vectors loaded successfully!")
                else:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Muat model
                    word2vec_model.load_model()
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    word2vec_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor untuk penggunaan di masa mendatang
                    vectors_dir = os.path.dirname(vectors_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    word2vec_model.save_verse_vectors(vectors_path)
            except Exception as e:
                print(f"Error initializing Word2Vec model: {e}")
                traceback.print_exc()
                raise e
        
        return word2vec_model
    
    elif model_type == 'fasttext':
        if fasttext_model is None:
            try:
                # Gunakan path yang relatif terhadap root project
                model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/fasttext/fasttext_model.model')
                fasttext_model = FastTextModel(model_path=model_path)
                
                # Cek apakah file vektor ayat sudah ada
                vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/fasttext_verses.pkl')
                
                if os.path.exists(vectors_path):
                    # Muat model dan vektor ayat yang sudah ada
                    fasttext_model.load_model()
                    fasttext_model.load_verse_vectors(vectors_path)
                    print(f"FastText model and verse vectors loaded successfully!")
                else:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Muat model
                    fasttext_model.load_model()
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    fasttext_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor untuk penggunaan di masa mendatang
                    vectors_dir = os.path.dirname(vectors_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    fasttext_model.save_verse_vectors(vectors_path)
            except Exception as e:
                print(f"Error initializing FastText model: {e}")
                traceback.print_exc()
                raise e
        
        return fasttext_model
    
    elif model_type == 'glove':
        if glove_model is None:
            try:
                # Gunakan path yang relatif terhadap root project
                model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/glove/alquran_vectors.txt')
                glove_model = GloVeModel(model_path=model_path)
                
                # Cek apakah file vektor ayat sudah ada
                vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/glove_verses.pkl')
                
                if os.path.exists(vectors_path):
                    # Muat model dan vektor ayat yang sudah ada
                    glove_model.load_model()
                    glove_model.load_verse_vectors(vectors_path)
                    print(f"GloVe model and verse vectors loaded successfully!")
                else:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Muat model
                    glove_model.load_model()
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    glove_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor untuk penggunaan di masa mendatang
                    vectors_dir = os.path.dirname(vectors_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    glove_model.save_verse_vectors(vectors_path)
            except Exception as e:
                print(f"Error initializing GloVe model: {e}")
                traceback.print_exc()
                raise e
        
        return glove_model
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def get_classification_path(index_id):
    """
    Mendapatkan path lengkap hierarki klasifikasi untuk indeks tertentu
    
    Args:
        index_id (int): ID indeks
        
    Returns:
        list: Path klasifikasi dari root hingga indeks yang diminta
    """
    if index_id is None:
        return []
    
    result = []
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Menggunakan algoritma iteratif untuk mendapatkan path
    current_id = index_id
    while current_id is not None:
        cursor.execute('''
            SELECT id, title, parent_id 
            FROM quran_index 
            WHERE id = ?
        ''', (current_id,))
        
        index = cursor.fetchone()
        if not index:
            break
            
        # Tambahkan indeks ini ke path (di bagian awal list)
        result.insert(0, {
            'id': index['id'],
            'title': index['title']
        })
        
        # Pindah ke parent
        current_id = index['parent_id']
    
    conn.close()
    return result

@api_bp.route('/search', methods=['POST'])
def search():
    """
    Endpoint untuk pencarian semantik
    """
    # Dapatkan parameter dari request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    model_type = data.get('model', 'word2vec')
    language = data.get('language', 'id')
    limit = int(data.get('limit', 10))
    threshold = float(data.get('threshold', 0.5))
    
    # Validasi model type
    if model_type not in ['word2vec', 'fasttext', 'glove']:
        return jsonify({'error': f'Unsupported model type: {model_type}'}), 400
    
    # Inisialisasi model yang dipilih
    try:
        model = init_model(model_type)
    except Exception as e:
        return jsonify({'error': f'Failed to initialize {model_type} model: {str(e)}'}), 500
    
    # Lakukan pencarian
    try:
        results = model.search(query, language, limit, threshold)
        
        # Tambahkan informasi klasifikasi untuk setiap hasil
        for result in results:
            # Dapatkan index_id berdasarkan surah dan ayat
            surah = result['surah_number']
            ayat = result['ayat_number']
            ayat_ref = f"{surah}:{ayat}"
            
            # Cari melalui list_ayat dalam format JSON
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, list_ayat 
                FROM quran_index 
                WHERE list_ayat IS NOT NULL
            ''')
            
            indexes_with_ayat = cursor.fetchall()
            conn.close()
            
            matching_indexes = []
            for idx in indexes_with_ayat:
                if idx['list_ayat']:
                    try:
                        ayat_list = json.loads(idx['list_ayat'])
                        if ayat_list and ayat_ref in ayat_list:
                            matching_indexes.append({
                                'id': idx['id'],
                                'title': idx['title']
                            })
                    except json.JSONDecodeError:
                        continue
            
            if matching_indexes:
                # Pilih klasifikasi pertama untuk breadcrumb path
                primary_classification = matching_indexes[0]
                result['classification'] = {
                    'id': primary_classification['id'],
                    'title': primary_classification['title'],
                    'path': get_classification_path(primary_classification['id'])
                }
                
                # Tambahkan semua klasifikasi terkait
                result['related_classifications'] = matching_indexes
            else:
                result['classification'] = None
                result['related_classifications'] = []
        
        # Tambahkan ke histori pencarian jika user sudah login
        if 'user_id' in session:
            add_search_history(session['user_id'], query, model_type, len(results))
            
            # Update statistik aplikasi
            # Increment total pencarian, dan tambahkan 1 user unik
            from backend.db import update_app_statistics
            update_app_statistics(
                searches=1,
                users=1,
                model=model_type,
                avg_results=len(results)
            )
        
        return jsonify({
            'query': query,
            'model': model_type,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        print(f"Search error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/models', methods=['GET'])
def get_models():
    """
    Endpoint untuk mendapatkan model yang tersedia
    """
    available_models = [
        {
            'id': 'word2vec',
            'name': 'Word2Vec',
            'description': 'Model yang mengubah kata menjadi vektor berdasarkan konteks dan mengidentifikasi hubungan semantik antar kata.'
        },
        {
            'id': 'fasttext',
            'name': 'FastText',
            'description': 'Model yang memperluas Word2Vec dengan menambahkan representasi sub-kata, sehingga dapat menangani kata yang tidak ada dalam kosakata (out-of-vocabulary words).'
        },
        {
            'id': 'glove',
            'name': 'GloVe',
            'description': 'Global Vectors for Word Representation. Model yang fokus pada statistik co-occurrence global, menangkap makna semantik dan sintaksis kata.'
        }
    ]
    
    return jsonify(available_models)

@api_bp.route('/user_settings', methods=['GET'])
def user_settings():
    """
    Endpoint untuk mendapatkan pengaturan pengguna
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    settings = get_user_settings(session['user_id'])
    
    return jsonify({
        'default_model': settings.get('default_model', 'word2vec'),
        'result_limit': settings.get('result_limit', 10),
        'threshold': settings.get('threshold', 0.5)
    })

# Endpoint untuk klasifikasi index Al-Quran

@api_bp.route('/quran/index', methods=['GET'])
def get_indexes():
    """
    Mendapatkan daftar index Al-Quran
    Query param:
    - parent_id: ID parent index (opsional)
    """
    parent_id = request.args.get('parent_id')
    
    # Konversi parent_id ke integer jika ada
    if parent_id:
        try:
            parent_id = int(parent_id)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Parameter parent_id harus berupa angka'
            }), 400
    
    indexes = get_quran_indexes(parent_id)
    
    # Tandai apakah index memiliki sub-index atau ayat
    for index in indexes:
        sub_indexes = get_quran_indexes(index['id'])
        ayat = get_quran_ayat_by_index(index['id'])
        
        index['has_children'] = len(sub_indexes) > 0
        index['has_ayat'] = len(ayat) > 0
        
        # Tambahkan info jumlah ayat
        index['ayat_count'] = len(ayat)
    
    return jsonify({
        'success': True,
        'data': indexes
    })

@api_bp.route('/quran/index/<int:index_id>', methods=['GET'])
def get_index_by_id(index_id):
    """
    Mendapatkan detail index Al-Quran berdasarkan ID
    """
    index = get_quran_index_by_id(index_id)
    
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    # Dapatkan sub-index dan ayat
    sub_indexes = get_quran_indexes(index_id)
    ayat = get_quran_ayat_by_index(index_id)
    
    # Dapatkan parent jika ada
    parent = None
    if index['parent_id']:
        parent = get_quran_index_by_id(index['parent_id'])
    
    return jsonify({
        'success': True,
        'data': {
            'index': index,
            'parent': parent,
            'sub_indexes': sub_indexes,
            'ayat': ayat
        }
    })

@api_bp.route('/quran/index', methods=['POST'])
def add_index():
    """
    Menambahkan index Al-Quran baru
    Memerlukan autentikasi sebagai admin
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Anda harus login untuk mengakses fitur ini'
        }), 401
    
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return jsonify({
            'success': False,
            'message': 'Anda tidak memiliki akses untuk fitur ini'
        }), 403
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Data tidak lengkap, title harus diisi'
        }), 400
    
    # Validasi parent_id jika ada
    parent_id = data.get('parent_id')
    level = 1
    
    if parent_id:
        parent = get_quran_index_by_id(parent_id)
        if not parent:
            return jsonify({
                'success': False,
                'message': 'Parent index tidak ditemukan'
            }), 404
        level = parent['level'] + 1
    
    success, result = add_quran_index(
        title=data['title'],
        description=data.get('description'),
        parent_id=parent_id,
        level=level,
        sort_order=data.get('sort_order', 0)
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Index berhasil ditambahkan',
            'data': {
                'id': result
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Gagal menambahkan index: {result}'
        }), 500

@api_bp.route('/quran/index/<int:index_id>', methods=['PUT'])
def update_index(index_id):
    """
    Memperbarui index Al-Quran
    Memerlukan autentikasi sebagai admin
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Anda harus login untuk mengakses fitur ini'
        }), 401
    
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return jsonify({
            'success': False,
            'message': 'Anda tidak memiliki akses untuk fitur ini'
        }), 403
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Data tidak lengkap, title harus diisi'
        }), 400
    
    # Periksa apakah index ada
    index = get_quran_index_by_id(index_id)
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    # Validasi parent_id jika ada
    parent_id = data.get('parent_id')
    level = 1
    
    if parent_id:
        # Validasi bahwa parent bukan dirinya sendiri atau anak dari index ini
        if parent_id == index_id:
            return jsonify({
                'success': False,
                'message': 'Parent tidak boleh dirinya sendiri'
            }), 400
            
        # Periksa apakah parent valid
        parent = get_quran_index_by_id(parent_id)
        if not parent:
            return jsonify({
                'success': False,
                'message': 'Parent index tidak ditemukan'
            }), 404
            
        # Hitung level baru
        level = parent['level'] + 1
    
    success, message = update_quran_index(
        index_id=index_id,
        title=data['title'],
        description=data.get('description'),
        parent_id=parent_id,
        level=level,
        sort_order=data.get('sort_order', 0)
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500

@api_bp.route('/quran/index/<int:index_id>', methods=['DELETE'])
def delete_index(index_id):
    """
    Menghapus index Al-Quran
    Memerlukan autentikasi sebagai admin
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Anda harus login untuk mengakses fitur ini'
        }), 401
    
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return jsonify({
            'success': False,
            'message': 'Anda tidak memiliki akses untuk fitur ini'
        }), 403
    
    # Periksa apakah index ada
    index = get_quran_index_by_id(index_id)
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    success, message = delete_quran_index(index_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500

@api_bp.route('/quran/index/tree', methods=['GET'])
def get_index_tree():
    """
    Mendapatkan seluruh index Al-Quran dalam format tree
    """
    def build_tree(parent_id=None):
        indexes = get_quran_indexes(parent_id)
        
        for index in indexes:
            index_id = index['id']
            
            # Check if has ayat
            ayat = get_quran_ayat_by_index(index_id)
            index['has_ayat'] = len(ayat) > 0
            index['ayat_count'] = len(ayat)
            
            # Get children recursively
            children = build_tree(index_id)
            if children:
                index['children'] = children
                index['has_children'] = True
            else:
                index['children'] = []
                index['has_children'] = False
        
        return indexes
    
    try:
        tree = build_tree()
        return jsonify({
            'success': True,
            'data': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat membangun tree: {str(e)}'
        }), 500

@api_bp.route('/quran/index/all', methods=['GET'])
def get_all_indexes():
    """
    Mendapatkan seluruh daftar index untuk keperluan dropdown, dll
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, parent_id, level FROM quran_index ORDER BY level, title')
    all_indexes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': all_indexes
    })

@api_bp.route('/quran/excel/sheets', methods=['POST'])
def get_excel_sheets():
    """
    Mendapatkan daftar sheet dari file Excel yang diupload
    """
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'Tidak ada file yang dikirim'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'Tidak ada file yang dipilih'
        }), 400
    
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({
            'success': False,
            'message': 'File harus berformat Excel (.xls atau .xlsx)'
        }), 400
    
    # Simpan file sementara dengan timestamp untuk mencegah konflik nama file
    import tempfile
    import time
    
    timestamp = int(time.time())
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{timestamp}_{file.filename}")
    
    try:
        # Simpan file ke tempat sementara
        file.save(temp_path)
        
        # Gunakan fungsi dari excel_importer.py
        from backend.excel_importer import get_excel_sheets
        success, result = get_excel_sheets(temp_path)
        
        if success:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat membaca file Excel: {str(e)}'
        }), 500
    finally:
        # Coba hapus file sementara
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Tidak dapat menghapus file sementara: {str(e)}")

@api_bp.route('/quran/excel/upload', methods=['POST'])
def upload_excel():
    """
    Upload dan memproses file Excel ke dalam database
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Anda harus login untuk mengakses fitur ini'
        }), 401
    
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return jsonify({
            'success': False,
            'message': 'Anda tidak memiliki akses untuk fitur ini'
        }), 403
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'Tidak ada file yang dikirim'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'Tidak ada file yang dipilih'
        }), 400
    
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({
            'success': False,
            'message': 'File harus berformat Excel (.xls atau .xlsx)'
        }), 400
    
    sheet_name = request.form.get('sheet_name')
    if not sheet_name:
        return jsonify({
            'success': False,
            'message': 'Nama sheet tidak diberikan'
        }), 400
    
    parent_id = request.form.get('parent_id')
    if parent_id:
        try:
            parent_id = int(parent_id)
            
            # Validasi parent_id
            parent = get_quran_index_by_id(parent_id)
            if not parent:
                return jsonify({
                    'success': False,
                    'message': 'Parent index tidak ditemukan'
                }), 404
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'ID parent harus berupa angka'
            }), 400
    else:
        parent_id = None
    
    # Simpan file sementara dengan timestamp untuk mencegah konflik nama file
    import tempfile
    import time
    
    timestamp = int(time.time())
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{timestamp}_{file.filename}")
    
    try:
        # Simpan file ke tempat sementara
        file.save(temp_path)
        
        # Gunakan fungsi dari excel_importer.py
        from backend.excel_importer import excel_to_hierarchy_db
        success, message = excel_to_hierarchy_db(temp_path, sheet_name, parent_id)
        
        # Hasil
        if success:
            result = {
                'success': True,
                'message': message
            }
        else:
            result = {
                'success': False,
                'message': message
            }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat memproses file: {str(e)}'
        }), 500
    finally:
        # Pastikan file dihapus apapun yang terjadi
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"Gagal menghapus file sementara: {str(e)}")

@api_bp.route('/quran/index/stats', methods=['GET'])
def get_quran_index_stats():
    """
    Mendapatkan statistik tentang index dan ayat Al-Quran
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Dapatkan statistik kategori/index berdasarkan level
        cursor.execute('''
        SELECT level, COUNT(*) as count 
        FROM quran_index 
        GROUP BY level 
        ORDER BY level
        ''')
        level_stats = [dict(row) for row in cursor.fetchall()]
        
        # Dapatkan jumlah total kategori
        cursor.execute('SELECT COUNT(*) as total FROM quran_index')
        total_categories = cursor.fetchone()['total']
        
        # Dapatkan statistik list_ayat
        cursor.execute('SELECT id, list_ayat FROM quran_index WHERE list_ayat IS NOT NULL')
        indexes_with_ayat = cursor.fetchall()
        
        # Hitung jumlah ayat dan kategori yang memiliki ayat
        total_ayat = 0
        categories_with_ayat = 0
        surah_counts = {}  # Untuk menghitung ayat berdasarkan surah
        
        import json
        
        for idx in indexes_with_ayat:
            if idx['list_ayat']:
                try:
                    ayat_list = json.loads(idx['list_ayat'])
                    if ayat_list and len(ayat_list) > 0:
                        categories_with_ayat += 1
                        total_ayat += len(ayat_list)
                        
                        # Hitung ayat per surah
                        for ayat_ref in ayat_list:
                            parts = ayat_ref.split(':')
                            if len(parts) == 2:
                                surah = parts[0]
                                if surah in surah_counts:
                                    surah_counts[surah] += 1
                                else:
                                    surah_counts[surah] = 1
                except json.JSONDecodeError:
                    continue
        
        # Format statistik surah
        surah_stats = []
        for surah, count in surah_counts.items():
            surah_stats.append({
                'surah': int(surah),
                'count': count
            })
        
        # Urutkan statistik surah berdasarkan nomor surah
        surah_stats.sort(key=lambda x: x['surah'])
        
        # Dapatkan jumlah kategori berdasarkan parent_id
        cursor.execute('''
        SELECT 
            CASE 
                WHEN parent_id IS NULL THEN 'Root' 
                ELSE 'Child' 
            END as category_type, 
            COUNT(*) as count 
        FROM quran_index 
        GROUP BY category_type
        ''')
        parent_type_stats = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'total_categories': total_categories,
                'total_ayat': total_ayat,
                'categories_with_ayat': categories_with_ayat,
                'level_stats': level_stats,
                'parent_type_stats': parent_type_stats,
                'surah_stats': surah_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat mendapatkan statistik: {str(e)}'
        }), 500
    finally:
        if conn:
            conn.close()

@api_bp.route('/statistics/overall', methods=['GET'])
def get_app_overall_stats():
    """
    Mendapatkan statistik keseluruhan penggunaan aplikasi
    """
    try:
        from backend.db import get_overall_statistics
        
        # Ambil statistik keseluruhan
        overall_stats = get_overall_statistics()
        
        # Dapatkan statistik 30 hari terakhir untuk tren
        from backend.db import get_app_statistics
        daily_stats = get_app_statistics()
        
        # Format daily_stats untuk chart
        dates = []
        searches = []
        users = []
        
        for stat in daily_stats:
            dates.append(stat['date'])
            searches.append(stat['total_searches'])
            users.append(stat['unique_users'])
        
        return jsonify({
            'success': True,
            'data': {
                'overall': overall_stats,
                'trends': {
                    'dates': dates,
                    'searches': searches,
                    'users': users
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat mendapatkan statistik keseluruhan: {str(e)}'
        }), 500

@api_bp.route('/statistics/daily', methods=['GET'])
def get_app_daily_stats():
    """
    Mendapatkan statistik harian penggunaan aplikasi
    """
    try:
        # Dapatkan parameter query
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        from backend.db import get_app_statistics
        
        # Ambil statistik berdasarkan parameter
        daily_stats = get_app_statistics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': daily_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat mendapatkan statistik harian: {str(e)}'
        }), 500

@api_bp.route('/surah', methods=['GET'])
def get_all_surah_list():
    """
    Mendapatkan daftar semua surah Al-Quran
    """
    try:
        from backend.db import get_all_surah
        
        surah_list = get_all_surah()
        
        return jsonify({
            'success': True,
            'data': surah_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat mendapatkan daftar surah: {str(e)}'
        }), 500

@api_bp.route('/surah/<int:surah_number>', methods=['GET'])
def get_surah_detail(surah_number):
    """
    Mendapatkan detail surah dan ayatnya
    """
    try:
        from backend.db import get_surah_by_number, get_verses_by_surah
        
        # Dapatkan informasi surah
        surah = get_surah_by_number(surah_number)
        
        if not surah:
            return jsonify({
                'success': False,
                'message': f'Surah dengan nomor {surah_number} tidak ditemukan'
            }), 404
        
        # Dapatkan ayat-ayat dari surah ini
        verses = get_verses_by_surah(surah_number)
        
        return jsonify({
            'success': True,
            'data': {
                'surah': surah,
                'verses': verses
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saat mendapatkan detail surah: {str(e)}'
        }), 500

@api_bp.route('/quran/index/roots', methods=['GET'])
def get_root_indexes():
    """
    Mendapatkan daftar indeks utama/root Al-Quran (tanpa parent)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, title, level 
    FROM quran_index 
    WHERE parent_id IS NULL 
    ORDER BY title
    ''')
    
    root_indexes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'data': root_indexes
    })

# Tambahkan endpoint baru untuk distribusi hasil pencarian berdasarkan klasifikasi
@api_bp.route('/search/distribution', methods=['POST'])
def search_distribution():
    """
    Endpoint untuk mendapatkan distribusi hasil pencarian berdasarkan kategori
    """
    # Dapatkan parameter dari request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Ambil hasil pencarian dari data
    search_results = data.get('results', [])
    if not search_results:
        return jsonify({'error': 'Hasil pencarian diperlukan'}), 400
    
    try:
        # Hitung distribusi klasifikasi
        classification_counts = {}
        
        for result in search_results:
            if 'classification' in result and result['classification']:
                classification_id = result['classification']['id']
                classification_title = result['classification']['title']
                
                if classification_id in classification_counts:
                    classification_counts[classification_id]['count'] += 1
                else:
                    classification_counts[classification_id] = {
                        'category': classification_title,
                        'count': 1
                    }
        
        # Konversi ke list untuk visualisasi
        distribution = list(classification_counts.values())
        
        # Urutkan berdasarkan jumlah hasil (terbanyak dulu)
        distribution.sort(key=lambda x: x['count'], reverse=True)
        
        # Jika tidak ada klasifikasi ditemukan
        if not distribution:
            return jsonify({
                'success': False,
                'message': 'Tidak ada informasi klasifikasi ditemukan dalam hasil pencarian'
            })
        
        return jsonify({
            'success': True,
            'data': distribution
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/quran/index/ayat/<int:index_id>', methods=['PUT'])
def update_index_ayat(index_id):
    """
    Memperbarui daftar ayat untuk sebuah index
    Memerlukan autentikasi sebagai admin
    """
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': 'Anda harus login untuk mengakses fitur ini'
        }), 401
    
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return jsonify({
            'success': False,
            'message': 'Anda tidak memiliki akses untuk fitur ini'
        }), 403
    
    data = request.json
    
    if not data or 'ayat_list' not in data:
        return jsonify({
            'success': False,
            'message': 'Data tidak lengkap, ayat_list harus diberikan'
        }), 400
    
    # Periksa apakah index ada
    index = get_quran_index_by_id(index_id)
    if not index:
        return jsonify({
            'success': False,
            'message': 'Index tidak ditemukan'
        }), 404
    
    # Update list_ayat
    from backend.db import update_quran_index_ayat
    success, message = update_quran_index_ayat(index_id, data['ayat_list'])
    
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500 