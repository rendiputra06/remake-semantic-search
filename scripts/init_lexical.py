#!/usr/bin/env python
"""
Script untuk menginisialisasi pencarian leksikal dan tesaurus sinonim bahasa Indonesia
"""
import os
import sys
import time
import argparse

# Tambahkan root project ke PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing import process_quran_data
from backend.lexical_search import LexicalSearch
from backend.thesaurus import IndonesianThesaurus

def init_lexical_search(dataset_dir):
    """
    Inisialisasi pencarian leksikal
    """
    print(f"Memulai inisialisasi pencarian leksikal dari {dataset_dir}")
    start_time = time.time()
    
    # Proses data Al-Quran
    print("Memproses data Al-Quran...")
    preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
    
    # Bangun indeks untuk pencarian leksikal
    print("Membangun indeks leksikal...")
    lexical_search = LexicalSearch()
    lexical_search.build_index(preprocessed_verses)
    
    print(f"Inisialisasi pencarian leksikal selesai dalam {time.time() - start_time:.2f} detik")

def init_thesaurus():
    """
    Inisialisasi tesaurus bahasa Indonesia
    """
    print("Memulai inisialisasi tesaurus bahasa Indonesia")
    start_time = time.time()
    
    # Buat tesaurus
    thesaurus = IndonesianThesaurus()
    
    # Buat tesaurus default (khusus Al-Quran) jika belum ada
    if not os.path.exists(thesaurus.custom_thesaurus_path):
        print("Membuat tesaurus default khusus Al-Quran...")
        thesaurus.create_default_thesaurus()
    
    print(f"Inisialisasi tesaurus selesai dalam {time.time() - start_time:.2f} detik")

def main():
    parser = argparse.ArgumentParser(description='Inisialisasi pencarian leksikal dan tesaurus')
    parser.add_argument('--component', choices=['lexical', 'thesaurus', 'all'], default='all',
                        help='Komponen yang diinisialisasi: lexical, thesaurus, atau all (default)')
    args = parser.parse_args()
    
    # Tentukan direktori dataset
    dataset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset/surah')
    
    if args.component in ['lexical', 'all']:
        init_lexical_search(dataset_dir)
    
    if args.component in ['thesaurus', 'all']:
        init_thesaurus()
    
    print("Inisialisasi selesai!")

if __name__ == '__main__':
    main() 