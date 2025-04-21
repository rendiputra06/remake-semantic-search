"""
Modul untuk melakukan preprocessing data Al-Quran
"""
import os
import json
import re
import string
from typing import List, Dict, Any

# --- KONSTANTA ---
STOPWORDS_ID = [
    'yang', 'dan', 'di', 'ini', 'itu', 'dengan', 'untuk', 'pada', 'tidak', 'adalah',
    'dari', 'dalam', 'akan', 'ke', 'juga', 'saya', 'kamu', 'dia', 'mereka', 'kami',
    'kita', 'ada', 'oleh', 'atau', 'sebagai', 'tetapi', 'bisa', 'dapat', 'sudah', 'belum',
    'yaitu', 'jika', 'maka', 'tentang', 'seperti', 'hanya', 'karena', 'secara', 'menjadi',
    'telah', 'bahwa', 'lebih', 'sangat', 'tersebut', 'hingga', 'harus', 'bagi', 'namun', 'ya',
    'apabila', 'ketika', 'sesungguhnya', 'wahai', 'hai', 'kepada', 'atas', 'merupakan'
]

# --- FUNGSI PREPROCESSING UMUM ---
def remove_punctuation(text: str) -> str:
    """Menghapus tanda baca dari teks"""
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)

def remove_stopwords(tokens: List[str], stopwords: List[str] = STOPWORDS_ID) -> List[str]:
    """Menghapus stopwords dari daftar token"""
    return [token for token in tokens if token.lower() not in stopwords]

def tokenize(text: str) -> List[str]:
    """Memecah teks menjadi token-token"""
    # Ubah ke lowercase
    text = text.lower()
    # Hapus tanda baca
    text = remove_punctuation(text)
    # Tokenisasi sederhana dengan memisahkan berdasarkan spasi
    tokens = text.split()
    return tokens

def preprocess_text(text: str, remove_stops: bool = True) -> List[str]:
    """Melakukan preprocessing lengkap pada teks"""
    tokens = tokenize(text)
    if remove_stops:
        tokens = remove_stopwords(tokens)
    return tokens

# --- FUNGSI PREPROCESSING KHUSUS AL-QURAN ---
def load_quran_data(dataset_dir: str) -> Dict[str, Any]:
    """
    Memuat semua data Al-Quran dari direktori dataset
    """
    quran_data = {}
    
    # Pastikan direktori ada
    if not os.path.exists(dataset_dir):
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
    
    print(f"Loading Quran data from {dataset_dir}")
    surah_files = [f for f in os.listdir(dataset_dir) if f.endswith('.json')]
    
    if not surah_files:
        raise FileNotFoundError(f"No JSON files found in {dataset_dir}")
    
    print(f"Found {len(surah_files)} surah files")
    
    for surah_file in surah_files:
        surah_path = os.path.join(dataset_dir, surah_file)
        try:
            with open(surah_path, 'r', encoding='utf-8') as file:
                surah_data = json.load(file)
                surah_number = os.path.splitext(surah_file)[0]
                quran_data[surah_number] = surah_data
                print(f"Loaded surah {surah_number}")
        except Exception as e:
            print(f"Error loading {surah_file}: {e}")
    
    print(f"Successfully loaded {len(quran_data)} surahs")
    return quran_data

def extract_verses(quran_data: Dict[str, Any], language: str = 'id') -> Dict[str, Dict[str, str]]:
    """
    Mengekstrak ayat-ayat Al-Quran dari data lengkap
    """
    verses = {}
    
    for surah_number, surah_data in quran_data.items():
        for surah_key, surah_content in surah_data.items():
            surah_name = surah_content.get('name_latin', '')
            
            # Dapatkan teks Arab
            arabic_texts = surah_content.get('text', {})
            
            # Dapatkan terjemahan
            translations = {}
            if language == 'id' and 'translations' in surah_content:
                if 'id' in surah_content['translations']:
                    translations = surah_content['translations']['id'].get('text', {})
            
            # Gabungkan data untuk setiap ayat
            for ayat_number, arabic_text in arabic_texts.items():
                verse_id = f"{surah_number}:{ayat_number}"
                translation = translations.get(ayat_number, '')
                
                verses[verse_id] = {
                    'surah_number': surah_number,
                    'surah_name': surah_name,
                    'ayat_number': ayat_number,
                    'arabic': arabic_text,
                    'translation': translation
                }
    
    print(f"Extracted {len(verses)} verses")
    return verses

def preprocess_quran_verses(verses: Dict[str, Dict[str, str]], language: str = 'id') -> Dict[str, Dict[str, Any]]:
    """
    Melakukan preprocessing pada ayat-ayat Al-Quran
    """
    preprocessed_verses = {}
    
    print(f"Preprocessing {len(verses)} verses...")
    
    for verse_id, verse_data in verses.items():
        # Ambil teks yang akan diproses berdasarkan bahasa
        if language == 'id':
            text_to_process = verse_data['translation']
        else:
            # Default ke terjemahan Indonesia jika bahasa tidak didukung
            text_to_process = verse_data['translation']
        
        # Lakukan preprocessing
        tokens = preprocess_text(text_to_process)
        
        # Simpan hasil
        preprocessed_verses[verse_id] = {
            'surah_number': verse_data['surah_number'],
            'surah_name': verse_data['surah_name'],
            'ayat_number': verse_data['ayat_number'],
            'arabic': verse_data['arabic'],
            'translation': verse_data['translation'],
            'tokens': tokens,
            'processed_text': ' '.join(tokens)
        }
    
    print(f"Preprocessing completed for {len(preprocessed_verses)} verses")
    return preprocessed_verses

def create_quran_corpus(preprocessed_verses: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Membuat korpus dari ayat-ayat Al-Quran yang telah diproses
    """
    corpus = []
    for verse_id, verse_data in preprocessed_verses.items():
        corpus.append(verse_data['processed_text'])
    
    return corpus

# Fungsi utama untuk melakukan preprocessing 
def process_quran_data(dataset_dir: str, language: str = 'id') -> Dict[str, Dict[str, Any]]:
    """
    Fungsi utama untuk memproses data Al-Quran
    """
    print(f"Starting Quran data processing from {dataset_dir}")
    
    # Load data
    quran_data = load_quran_data(dataset_dir)
    
    # Ekstrak ayat-ayat
    verses = extract_verses(quran_data, language)
    
    # Lakukan preprocessing
    preprocessed_verses = preprocess_quran_verses(verses, language)
    
    return preprocessed_verses 