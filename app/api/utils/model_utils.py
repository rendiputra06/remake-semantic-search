"""
Utility functions for model management and classification
"""
import os
import traceback
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
from backend.db import get_db_connection

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
                # Gunakan default path dari backend model agar robust di Docker
                word2vec_model = Word2VecModel()
                
                # Muat model
                word2vec_model.load_model()
                # Coba muat vektor dengan path default backend
                try:
                    word2vec_model.load_verse_vectors()
                    print("Word2Vec verse vectors loaded (default path)")
                except Exception:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    word2vec_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor ke path default backend
                    vectors_dir = os.path.dirname(word2vec_model.vector_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    word2vec_model.save_verse_vectors(word2vec_model.vector_path)
            except Exception as e:
                print(f"Error initializing Word2Vec model: {e}")
                traceback.print_exc()
                raise e
        
        return word2vec_model
    
    elif model_type == 'fasttext':
        if fasttext_model is None:
            try:
                # Gunakan default path dari backend model agar robust di Docker
                fasttext_model = FastTextModel()
                
                # Muat model
                fasttext_model.load_model()
                # Coba muat vektor default backend
                try:
                    fasttext_model.load_verse_vectors()
                    print("FastText verse vectors loaded (default path)")
                except Exception:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    fasttext_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor ke path default backend
                    vectors_dir = os.path.dirname(fasttext_model.vector_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    fasttext_model.save_verse_vectors(fasttext_model.vector_path)
            except Exception as e:
                print(f"Error initializing FastText model: {e}")
                traceback.print_exc()
                raise e
        
        return fasttext_model
    
    elif model_type == 'glove':
        if glove_model is None:
            try:
                # Gunakan default path dari backend model agar robust di Docker
                glove_model = GloVeModel()
                
                # Muat model
                glove_model.load_model()
                # Coba muat vektor default backend
                try:
                    glove_model.load_verse_vectors()
                    print("GloVe verse vectors loaded (default path)")
                except Exception:
                    # Buat vektor ayat baru
                    from backend.preprocessing import process_quran_data
                    
                    # Proses data Al-Quran
                    print("Processing Quran data...")
                    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dataset/surah')
                    preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
                    
                    # Buat vektor ayat
                    glove_model.create_verse_vectors(preprocessed_verses)
                    
                    # Simpan vektor ke path default backend
                    vectors_dir = os.path.dirname(glove_model.vector_path)
                    os.makedirs(vectors_dir, exist_ok=True)
                    glove_model.save_verse_vectors(glove_model.vector_path)
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