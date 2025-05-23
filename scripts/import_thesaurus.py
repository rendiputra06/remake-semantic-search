#!/usr/bin/env python
"""
Script untuk mengimpor data relasi tesaurus dari CSV/Excel ke database
"""
import os
import sqlite3
import argparse
import csv
import pandas as pd
from datetime import datetime
import json

# Path ke database
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
LEXICAL_DB = os.path.join(DB_DIR, 'lexical.db')
THESAURUS_STATUS = os.path.join(DB_DIR, 'thesaurus_status.json')

def import_thesaurus_relations(input_file, relation_type='synonym', overwrite=False):
    """Import data relasi tesaurus dari CSV/Excel ke database"""
    if not os.path.exists(input_file):
        print(f"File input tidak ditemukan: {input_file}")
        return False
    
    # Periksa apakah database sudah ada
    if not os.path.exists(LEXICAL_DB):
        print("Database lexical belum diinisialisasi. Silakan inisialisasi dulu.")
        return False
    
    # Pastikan jenis relasi valid
    valid_relation_types = {
        'synonym': 'synonyms',
        'antonym': 'antonyms',
        'hyponym': 'hyponyms',
        'hypernym': 'hypernyms'
    }
    
    if relation_type not in valid_relation_types:
        print(f"Jenis relasi tidak valid: {relation_type}. Gunakan salah satu dari: {', '.join(valid_relation_types.keys())}")
        return False
    
    # Tentukan tabel berdasarkan jenis relasi
    relation_table = valid_relation_types[relation_type]
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Jika diminta untuk menimpa data yang sudah ada
    if overwrite:
        print(f"Menghapus data {relation_type} yang sudah ada...")
        cursor.execute(f"DELETE FROM {relation_table}")
        conn.commit()
    
    # Baca file berdasarkan ekstensi
    file_ext = os.path.splitext(input_file)[1].lower()
    
    try:
        # Data relasi yang akan dimasukkan
        relations = []
        
        if file_ext == '.csv':
            # Baca file CSV
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Ambil header
                
                # Periksa header
                if len(header) < 2:
                    print("Format CSV tidak valid. Minimal harus memiliki kolom kata1 dan kata2.")
                    return False
                
                # Tentukan indeks kolom
                word1_idx = 0  # Asumsi kolom pertama adalah kata1
                word2_idx = 1  # Asumsi kolom kedua adalah kata2
                strength_idx = 2 if len(header) > 2 else None  # Kolom ketiga adalah kekuatan jika ada
                
                # Baca data relasi
                for row in reader:
                    if len(row) > 1:
                        word1 = row[word1_idx].strip()
                        word2 = row[word2_idx].strip()
                        strength = float(row[strength_idx]) if strength_idx and len(row) > strength_idx and row[strength_idx] else 1.0
                        
                        if word1 and word2:  # Pastikan kedua kata tidak kosong
                            relations.append((word1, word2, strength))
        
        elif file_ext in ['.xlsx', '.xls']:
            # Baca file Excel
            df = pd.read_excel(input_file)
            
            # Periksa kolom
            if len(df.columns) < 2:
                print("Format Excel tidak valid. Minimal harus memiliki kolom kata1 dan kata2.")
                return False
            
            # Baca data relasi
            for _, row in df.iterrows():
                word1 = str(row[0]).strip()
                word2 = str(row[1]).strip()
                strength = float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else 1.0
                
                if word1 and word2 and word1 != "nan" and word2 != "nan":  # Pastikan kedua kata tidak kosong atau NaN
                    relations.append((word1, word2, strength))
        
        else:
            print(f"Format file tidak didukung: {file_ext}. Silakan gunakan CSV atau Excel.")
            return False
        
        # Masukkan data ke database
        if relations:
            print(f"Memproses {len(relations)} relasi {relation_type}...")
            
            # Pertama, pastikan semua kata ada di database lexical
            all_words = set()
            for word1, word2, _ in relations:
                all_words.add(word1)
                all_words.add(word2)
            
            # Periksa kata mana yang belum ada di database
            word_ids = {}
            for word in all_words:
                cursor.execute("SELECT id FROM lexical WHERE word = ?", (word,))
                result = cursor.fetchone()
                
                if result:
                    word_ids[word] = result[0]
                else:
                    # Tambahkan kata baru ke database lexical
                    cursor.execute(
                        "INSERT INTO lexical (word, definition, example) VALUES (?, ?, ?)",
                        (word, "", "")
                    )
                    word_ids[word] = cursor.lastrowid
            
            conn.commit()
            
            # Tentukan kolom untuk relasi berdasarkan jenis
            if relation_type == 'synonym':
                col1, col2 = 'word_id', 'synonym_id'
            elif relation_type == 'antonym':
                col1, col2 = 'word_id', 'antonym_id'
            elif relation_type == 'hyponym':
                col1, col2 = 'word_id', 'hyponym_id'
            elif relation_type == 'hypernym':
                col1, col2 = 'word_id', 'hypernym_id'
            
            # Tambahkan relasi ke database
            for word1, word2, strength in relations:
                try:
                    if relation_type in ['synonym', 'antonym']:
                        cursor.execute(
                            f"INSERT OR REPLACE INTO {relation_table} ({col1}, {col2}, strength) VALUES (?, ?, ?)",
                            (word_ids[word1], word_ids[word2], strength)
                        )
                    else:
                        cursor.execute(
                            f"INSERT OR REPLACE INTO {relation_table} ({col1}, {col2}) VALUES (?, ?)",
                            (word_ids[word1], word_ids[word2])
                        )
                except sqlite3.IntegrityError:
                    # Lewati jika ada konflik
                    pass
            
            conn.commit()
            
            # Update status tesaurus
            update_thesaurus_status(conn)
            
            print(f"Berhasil mengimpor {len(relations)} relasi {relation_type}.")
            return True
        else:
            print("Tidak ada relasi valid yang ditemukan di file.")
            return False
    
    except Exception as e:
        print(f"Error saat mengimpor data tesaurus: {e}")
        return False
    
    finally:
        conn.close()

def update_thesaurus_status(conn):
    """Update status database tesaurus berdasarkan jumlah kata dan relasi"""
    cursor = conn.cursor()
    
    # Hitung total kata unik yang terlibat dalam relasi
    cursor.execute("""
    SELECT COUNT(DISTINCT id) FROM lexical 
    WHERE id IN (
        SELECT word_id FROM synonyms 
        UNION 
        SELECT synonym_id FROM synonyms
        UNION
        SELECT word_id FROM antonyms
        UNION
        SELECT antonym_id FROM antonyms
        UNION
        SELECT word_id FROM hyponyms
        UNION
        SELECT hyponym_id FROM hyponyms
        UNION
        SELECT word_id FROM hypernyms
        UNION
        SELECT hypernym_id FROM hypernyms
    )
    """)
    word_count = cursor.fetchone()[0]
    
    # Hitung total relasi
    cursor.execute("SELECT COUNT(*) FROM synonyms")
    synonym_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM antonyms")
    antonym_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hyponyms")
    hyponym_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hypernyms")
    hypernym_count = cursor.fetchone()[0]
    
    relation_count = synonym_count + antonym_count + hyponym_count + hypernym_count
    
    # Update status
    status = {
        'initialized': True,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'word_count': word_count,
        'relation_count': relation_count,
        'synonym_count': synonym_count,
        'antonym_count': antonym_count,
        'hyponym_count': hyponym_count,
        'hypernym_count': hypernym_count
    }
    
    with open(THESAURUS_STATUS, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Import relasi tesaurus dari CSV/Excel ke database")
    parser.add_argument('input_file', type=str, help='Path ke file CSV/Excel yang berisi data relasi')
    parser.add_argument('--type', choices=['synonym', 'antonym', 'hyponym', 'hypernym'], default='synonym',
                       help='Jenis relasi yang akan diimpor')
    parser.add_argument('--overwrite', action='store_true', help='Hapus relasi yang sudah ada sebelum mengimpor')
    
    args = parser.parse_args()
    
    import_thesaurus_relations(args.input_file, args.type, args.overwrite)

if __name__ == "__main__":
    main() 