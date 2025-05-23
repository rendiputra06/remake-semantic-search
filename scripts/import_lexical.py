#!/usr/bin/env python
"""
Script untuk mengimpor data lexical dari CSV/Excel ke database
"""
import os
import sqlite3
import argparse
import csv
import pandas as pd
from datetime import datetime

# Path ke database
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
LEXICAL_DB = os.path.join(DB_DIR, 'lexical.db')
LEXICAL_STATUS = os.path.join(DB_DIR, 'lexical_status.json')

def import_lexical_data(input_file, overwrite=False):
    """Import data lexical dari CSV/Excel ke database"""
    if not os.path.exists(input_file):
        print(f"File input tidak ditemukan: {input_file}")
        return False
    
    # Periksa apakah database sudah ada
    if not os.path.exists(LEXICAL_DB):
        print("Database lexical belum diinisialisasi. Silakan inisialisasi dulu.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Jika diminta untuk menimpa data yang sudah ada
    if overwrite:
        print("Menghapus data lexical yang sudah ada...")
        cursor.execute("DELETE FROM lexical")
        conn.commit()
    
    # Baca file berdasarkan ekstensi
    file_ext = os.path.splitext(input_file)[1].lower()
    
    try:
        if file_ext == '.csv':
            # Baca file CSV
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Ambil header
                
                # Periksa header
                if len(header) < 2:
                    print("Format CSV tidak valid. Minimal harus memiliki kolom kata dan definisi.")
                    return False
                
                # Tentukan indeks kolom
                word_idx = 0  # Asumsi kolom pertama adalah kata
                def_idx = 1   # Asumsi kolom kedua adalah definisi
                example_idx = 2 if len(header) > 2 else None  # Kolom ketiga adalah contoh jika ada
                
                # Persiapkan data untuk dimasukkan
                data = []
                for row in reader:
                    if len(row) > 0:
                        word = row[word_idx].strip()
                        definition = row[def_idx].strip() if len(row) > def_idx else ""
                        example = row[example_idx] if example_idx and len(row) > example_idx else ""
                        
                        if word:  # Pastikan kata tidak kosong
                            data.append((word, definition, example))
        
        elif file_ext in ['.xlsx', '.xls']:
            # Baca file Excel
            df = pd.read_excel(input_file)
            
            # Periksa kolom
            if len(df.columns) < 2:
                print("Format Excel tidak valid. Minimal harus memiliki kolom kata dan definisi.")
                return False
            
            # Ambil data
            data = []
            for _, row in df.iterrows():
                word = str(row[0]).strip()
                definition = str(row[1]).strip() if len(row) > 1 else ""
                example = str(row[2]) if len(row) > 2 else ""
                
                if word and word != "nan":  # Pastikan kata tidak kosong dan bukan NaN
                    data.append((word, definition, example))
        
        else:
            print(f"Format file tidak didukung: {file_ext}. Silakan gunakan CSV atau Excel.")
            return False
        
        # Masukkan data ke database
        print(f"Mengimpor {len(data)} entri ke database lexical...")
        cursor.executemany(
            "INSERT OR REPLACE INTO lexical (word, definition, example, updated_at) VALUES (?, ?, ?, datetime('now'))",
            data
        )
        conn.commit()
        
        # Update status
        cursor.execute("SELECT COUNT(*) FROM lexical")
        entry_count = cursor.fetchone()[0]
        
        # Update status file
        update_lexical_status(entry_count)
        
        print(f"Berhasil mengimpor {len(data)} entri ke database lexical. Total entri: {entry_count}")
        return True
    
    except Exception as e:
        print(f"Error saat mengimpor data: {e}")
        return False
    
    finally:
        conn.close()

def update_lexical_status(entry_count):
    """Update status database lexical"""
    import json
    
    status = {
        'initialized': True,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'entry_count': entry_count
    }
    
    with open(LEXICAL_STATUS, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Import data lexical dari CSV/Excel ke database")
    parser.add_argument('input_file', type=str, help='Path ke file CSV/Excel yang berisi data lexical')
    parser.add_argument('--overwrite', action='store_true', help='Hapus data yang sudah ada sebelum mengimpor')
    
    args = parser.parse_args()
    
    import_lexical_data(args.input_file, args.overwrite)

if __name__ == "__main__":
    main() 