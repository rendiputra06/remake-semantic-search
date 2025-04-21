"""
Script untuk menginisialisasi sistem dengan model FastText
"""
import os
import sys

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.initialize import initialize_system

if __name__ == "__main__":
    # Jalankan inisialisasi khusus untuk model FastText
    print("Menginisialisasi sistem dengan model FastText...")
    initialize_system('fasttext')
    print("Inisialisasi FastText selesai!") 