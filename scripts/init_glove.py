"""
Script untuk menginisialisasi sistem dengan model GloVe
"""
import os
import sys

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.initialize import initialize_system

if __name__ == "__main__":
    # Jalankan inisialisasi khusus untuk model GloVe
    print("Menginisialisasi sistem dengan model GloVe...")
    initialize_system('glove')
    print("Inisialisasi GloVe selesai!") 