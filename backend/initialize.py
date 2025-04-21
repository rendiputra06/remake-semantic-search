"""
Script untuk menginisialisasi dan mempersiapkan model dan data
"""
import os
import sys
import traceback

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.preprocessing import process_quran_data
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel

def initialize_system(model_type='all'):
    """
    Fungsi utama untuk menginisialisasi sistem
    
    Args:
        model_type: Tipe model yang akan diinisialisasi ('word2vec', 'fasttext', 'glove', atau 'all')
    """
    print("Memulai inisialisasi sistem pencarian semantik Al-Quran...")
    
    # 1. Proses data Al-Quran
    print("\n--- PEMROSESAN DATA AL-QURAN ---")
    try:
        # Gunakan path yang relatif terhadap root project
        dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
        print(f"Berhasil memproses {len(preprocessed_verses)} ayat Al-Quran")
    except Exception as e:
        print(f"Error saat memproses data Al-Quran: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # 2. Inisialisasi model-model yang diminta
    if model_type == 'word2vec' or model_type == 'all':
        initialize_word2vec(preprocessed_verses)
    
    if model_type == 'fasttext' or model_type == 'all':
        initialize_fasttext(preprocessed_verses)
    
    if model_type == 'glove' or model_type == 'all':
        initialize_glove(preprocessed_verses)
    
    print("\nInisialisasi sistem selesai!")
    print("Sistem pencarian semantik Al-Quran siap digunakan.")

def initialize_word2vec(preprocessed_verses):
    """
    Inisialisasi model Word2Vec
    """
    print("\n--- INISIALISASI MODEL WORD2VEC ---")
    try:
        # Gunakan path model yang relatif terhadap root project
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/idwiki_word2vec/idwiki_word2vec_200_new_lower.model')
        
        word2vec_model = Word2VecModel(model_path=model_path)
        word2vec_model.load_model()
        
        # Buat vektor ayat
        print("Membuat vektor ayat dengan Word2Vec...")
        word2vec_model.create_verse_vectors(preprocessed_verses)
        
        # Simpan vektor untuk penggunaan di masa mendatang
        vectors_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors')
        os.makedirs(vectors_dir, exist_ok=True)
        vectors_path = os.path.join(vectors_dir, 'word2vec_verses.pkl')
        
        word2vec_model.save_verse_vectors(vectors_path)
        print(f"Vektor ayat Word2Vec disimpan di {vectors_path}")
    except Exception as e:
        print(f"Error saat inisialisasi model Word2Vec: {e}")
        traceback.print_exc()

def initialize_fasttext(preprocessed_verses):
    """
    Inisialisasi model FastText
    """
    print("\n--- INISIALISASI MODEL FASTTEXT ---")
    try:
        # Gunakan path model yang relatif terhadap root project
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/fasttext/fasttext_model.model')
        
        fasttext_model = FastTextModel(model_path=model_path)
        fasttext_model.load_model()
        
        # Buat vektor ayat
        print("Membuat vektor ayat dengan FastText...")
        fasttext_model.create_verse_vectors(preprocessed_verses)
        
        # Simpan vektor untuk penggunaan di masa mendatang
        vectors_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors')
        os.makedirs(vectors_dir, exist_ok=True)
        vectors_path = os.path.join(vectors_dir, 'fasttext_verses.pkl')
        
        fasttext_model.save_verse_vectors(vectors_path)
        print(f"Vektor ayat FastText disimpan di {vectors_path}")
    except Exception as e:
        print(f"Error saat inisialisasi model FastText: {e}")
        traceback.print_exc()

def initialize_glove(preprocessed_verses):
    """
    Inisialisasi model GloVe
    """
    print("\n--- INISIALISASI MODEL GLOVE ---")
    try:
        # Gunakan path model yang relatif terhadap root project
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/glove/alquran_vectors.txt')
        
        glove_model = GloVeModel(model_path=model_path)
        glove_model.load_model()
        
        # Buat vektor ayat
        print("Membuat vektor ayat dengan GloVe...")
        glove_model.create_verse_vectors(preprocessed_verses)
        
        # Simpan vektor untuk penggunaan di masa mendatang
        vectors_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors')
        os.makedirs(vectors_dir, exist_ok=True)
        vectors_path = os.path.join(vectors_dir, 'glove_verses.pkl')
        
        glove_model.save_verse_vectors(vectors_path)
        print(f"Vektor ayat GloVe disimpan di {vectors_path}")
    except Exception as e:
        print(f"Error saat inisialisasi model GloVe: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Pastikan kita berada di direktori yang benar
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Jalankan inisialisasi dengan parameter model yang diinginkan
    # Gunakan parameter 'word2vec', 'fasttext', 'glove', atau 'all'
    if len(sys.argv) > 1:
        model_type = sys.argv[1]
        initialize_system(model_type)
    else:
        # Default: inisialisasi semua model
        initialize_system('all') 