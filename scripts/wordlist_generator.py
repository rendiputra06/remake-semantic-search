#!/usr/bin/env python
"""
Script untuk menghasilkan daftar kata umum Bahasa Indonesia
untuk digunakan sebagai input ke script pengayaan tesaurus
"""
import os
import re
import argparse
from collections import Counter
from tqdm import tqdm
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

def clean_text(text):
    """Membersihkan teks dari karakter khusus dan mengubah ke lowercase"""
    # Hapus karakter khusus, simpan hanya huruf, angka, dan spasi
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    # Hapus angka
    text = re.sub(r'\d+', ' ', text)
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_words_from_file(file_path, min_word_length=3):
    """Mengekstrak kata-kata dari file teks"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Bersihkan teks
        clean = clean_text(text)
        
        # Pisahkan kata-kata
        words = clean.split()
        
        # Filter kata-kata berdasarkan panjang
        words = [word for word in words if len(word) >= min_word_length]
        
        return words
    except Exception as e:
        print(f"Error extracting words from {file_path}: {e}")
        return []

def process_directory(directory, min_word_length=3, min_frequency=2):
    """Memproses semua file teks dalam direktori untuk menghasilkan daftar kata umum"""
    word_counter = Counter()
    
    # Temukan semua file teks dalam direktori
    text_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                text_files.append(os.path.join(root, file))
    
    if not text_files:
        print(f"No text files found in directory: {directory}")
        return []
    
    print(f"Processing {len(text_files)} text files...")
    
    # Proses setiap file teks
    for file_path in tqdm(text_files):
        words = extract_words_from_file(file_path, min_word_length)
        word_counter.update(words)
    
    # Filter kata-kata berdasarkan frekuensi
    common_words = [word for word, count in word_counter.items() if count >= min_frequency]
    
    print(f"Found {len(common_words)} common words")
    return common_words

def extract_words_from_quran_dataset(directory):
    """Ekstrak kata-kata khusus dari dataset Al-Quran"""
    word_counter = Counter()
    
    # Cari folder surah dalam dataset
    surah_dir = os.path.join(directory, 'surah')
    if not os.path.exists(surah_dir):
        print(f"Surah directory not found: {surah_dir}")
        return []
    
    # Temukan semua file JSON dalam direktori
    json_files = []
    for root, _, files in os.walk(surah_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        print(f"No JSON files found in directory: {surah_dir}")
        return []
    
    print(f"Processing {len(json_files)} Quran JSON files...")
    
    import json
    
    # Proses setiap file JSON
    for file_path in tqdm(json_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Format struktur JSON yang benar berdasarkan file contoh:
                # {
                #    "nomor_surah": {
                #       "translations": {
                #           "id": {
                #               "text": {
                #                   "1": "Terjemahan ayat 1",
                #                   "2": "Terjemahan ayat 2",
                #                   ...
                #               }
                #           }
                #       }
                #    }
                # }
                
                # Ambil nomor surah (kunci pertama dalam data)
                if len(data) > 0:
                    surah_number = list(data.keys())[0]
                    surah_data = data[surah_number]
                    
                    # Cek apakah memiliki translations.id.text
                    if ('translations' in surah_data and 
                        'id' in surah_data['translations'] and 
                        'text' in surah_data['translations']['id']):
                        
                        # Ambil semua terjemahan ayat
                        translations = surah_data['translations']['id']['text']
                        for verse_num, translation in translations.items():
                            words = clean_text(translation).split()
                            word_counter.update([w for w in words if len(w) >= 3])
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Ambil kata-kata yang muncul minimal 3 kali
    common_words = [word for word, count in word_counter.items() if count >= 3 and len(word) >= 3]
    
    print(f"Found {len(common_words)} common words from Quran dataset")
    return common_words

def create_stemmed_wordlist(word_list):
    """Membuat daftar kata dasar menggunakan Sastrawi stemmer"""
    stemmer = StemmerFactory().create_stemmer()
    stemmed_words = set()
    
    print("Stemming words...")
    for word in tqdm(word_list):
        stemmed = stemmer.stem(word)
        if len(stemmed) >= 3:  # Hanya simpan kata dasar dengan panjang minimal 3
            stemmed_words.add(stemmed)
    
    return list(stemmed_words)

def save_wordlist(words, output_file):
    """Menyimpan daftar kata ke file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in sorted(words):
            f.write(f"{word}\n")
    
    print(f"Saved {len(words)} words to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate common Indonesian words list")
    parser.add_argument('--input-dir', type=str, help='Directory containing text files to process')
    parser.add_argument('--quran-dataset', type=str, help='Path to Quran dataset directory')
    parser.add_argument('--output', type=str, default='wordlist.txt', help='Output file path')
    parser.add_argument('--min-length', type=int, default=3, help='Minimum word length')
    parser.add_argument('--min-frequency', type=int, default=2, help='Minimum word frequency')
    parser.add_argument('--stem', action='store_true', help='Generate stemmed word list')
    
    args = parser.parse_args()
    
    all_words = set()
    
    # Ekstrak kata-kata dari direktori input jika disediakan
    if args.input_dir:
        if os.path.isdir(args.input_dir):
            words = process_directory(args.input_dir, args.min_length, args.min_frequency)
            all_words.update(words)
        else:
            print(f"Input directory not found: {args.input_dir}")
    
    # Ekstrak kata-kata dari dataset Al-Quran jika disediakan
    if args.quran_dataset:
        if os.path.isdir(args.quran_dataset):
            words = extract_words_from_quran_dataset(args.quran_dataset)
            all_words.update(words)
        else:
            print(f"Quran dataset directory not found: {args.quran_dataset}")
    
    # Buat daftar kata dasar jika diminta
    if args.stem and all_words:
        all_words = create_stemmed_wordlist(all_words)
    
    # Simpan daftar kata jika tidak kosong
    if all_words:
        save_wordlist(all_words, args.output)
    else:
        print("No words found. Please provide a valid input directory or Quran dataset.")

if __name__ == "__main__":
    main() 