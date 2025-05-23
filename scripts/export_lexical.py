#!/usr/bin/env python
"""
Script untuk mengekspor data dari database lexical dan tesaurus ke CSV
"""
import os
import csv
import sqlite3
import argparse
import json
from datetime import datetime

# Path ke database
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
LEXICAL_DB = os.path.join(DB_DIR, 'lexical.db')
EXPORT_DIR = os.path.join(DB_DIR, 'exports')

def export_lexical_data(output_file=None):
    """Ekspor data lexical ke CSV"""
    if not os.path.exists(LEXICAL_DB):
        print("Database lexical belum diinisialisasi.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Ambil semua data dari tabel lexical
    cursor.execute('SELECT id, word, definition, example, created_at, updated_at FROM lexical ORDER BY word')
    lexical_data = cursor.fetchall()
    
    # Buat direktori export jika belum ada
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Tentukan nama file output
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(EXPORT_DIR, f'lexical_export_{timestamp}.csv')
    else:
        output_file = os.path.join(EXPORT_DIR, output_file)
    
    # Tulis data ke CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Tulis header
            writer.writerow(['id', 'kata', 'definisi', 'contoh', 'dibuat_pada', 'diperbarui_pada'])
            # Tulis data
            writer.writerows(lexical_data)
        
        print(f"Data lexical berhasil diekspor ke {output_file}. Total {len(lexical_data)} entri.")
        return output_file
    except Exception as e:
        print(f"Error saat mengekspor data lexical: {e}")
        return False
    finally:
        conn.close()

def export_synonyms(output_file=None):
    """Ekspor data sinonim ke CSV"""
    if not os.path.exists(LEXICAL_DB):
        print("Database tesaurus belum diinisialisasi.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ambil data sinonim dengan nama kata
    cursor.execute('''
    SELECT s.id, w1.word as word, w2.word as synonym, s.strength, s.created_at
    FROM synonyms s
    JOIN lexical w1 ON s.word_id = w1.id
    JOIN lexical w2 ON s.synonym_id = w2.id
    ORDER BY w1.word
    ''')
    synonym_data = cursor.fetchall()
    
    # Buat direktori export jika belum ada
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Tentukan nama file output
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(EXPORT_DIR, f'synonyms_export_{timestamp}.csv')
    else:
        output_file = os.path.join(EXPORT_DIR, output_file)
    
    # Tulis data ke CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Tulis header
            writer.writerow(['id', 'kata', 'sinonim', 'kekuatan', 'dibuat_pada'])
            # Tulis data
            writer.writerows([dict(row) for row in synonym_data])
        
        print(f"Data sinonim berhasil diekspor ke {output_file}. Total {len(synonym_data)} relasi.")
        return output_file
    except Exception as e:
        print(f"Error saat mengekspor data sinonim: {e}")
        return False
    finally:
        conn.close()

def export_antonyms(output_file=None):
    """Ekspor data antonim ke CSV"""
    if not os.path.exists(LEXICAL_DB):
        print("Database tesaurus belum diinisialisasi.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ambil data antonim dengan nama kata
    cursor.execute('''
    SELECT a.id, w1.word as word, w2.word as antonym, a.strength, a.created_at
    FROM antonyms a
    JOIN lexical w1 ON a.word_id = w1.id
    JOIN lexical w2 ON a.antonym_id = w2.id
    ORDER BY w1.word
    ''')
    antonym_data = cursor.fetchall()
    
    # Buat direktori export jika belum ada
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Tentukan nama file output
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(EXPORT_DIR, f'antonyms_export_{timestamp}.csv')
    else:
        output_file = os.path.join(EXPORT_DIR, output_file)
    
    # Tulis data ke CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Tulis header
            writer.writerow(['id', 'kata', 'antonim', 'kekuatan', 'dibuat_pada'])
            # Tulis data
            writer.writerows([dict(row) for row in antonym_data])
        
        print(f"Data antonim berhasil diekspor ke {output_file}. Total {len(antonym_data)} relasi.")
        return output_file
    except Exception as e:
        print(f"Error saat mengekspor data antonim: {e}")
        return False
    finally:
        conn.close()

def export_all_thesaurus_relations(output_file=None):
    """Ekspor semua relasi tesaurus ke CSV"""
    if not os.path.exists(LEXICAL_DB):
        print("Database tesaurus belum diinisialisasi.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Ambil semua jenis relasi
    relations = []
    
    # Sinonim
    cursor.execute('''
    SELECT w1.word as word1, w2.word as word2, 'synonym' as relation_type, s.strength
    FROM synonyms s
    JOIN lexical w1 ON s.word_id = w1.id
    JOIN lexical w2 ON s.synonym_id = w2.id
    ''')
    relations.extend(cursor.fetchall())
    
    # Antonim
    cursor.execute('''
    SELECT w1.word as word1, w2.word as word2, 'antonym' as relation_type, a.strength
    FROM antonyms a
    JOIN lexical w1 ON a.word_id = w1.id
    JOIN lexical w2 ON a.antonym_id = w2.id
    ''')
    relations.extend(cursor.fetchall())
    
    # Hiponim
    cursor.execute('''
    SELECT w1.word as word1, w2.word as word2, 'hyponym' as relation_type, 1.0 as strength
    FROM hyponyms h
    JOIN lexical w1 ON h.word_id = w1.id
    JOIN lexical w2 ON h.hyponym_id = w2.id
    ''')
    relations.extend(cursor.fetchall())
    
    # Hipernim
    cursor.execute('''
    SELECT w1.word as word1, w2.word as word2, 'hypernym' as relation_type, 1.0 as strength
    FROM hypernyms h
    JOIN lexical w1 ON h.word_id = w1.id
    JOIN lexical w2 ON h.hypernym_id = w2.id
    ''')
    relations.extend(cursor.fetchall())
    
    # Buat direktori export jika belum ada
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Tentukan nama file output
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(EXPORT_DIR, f'thesaurus_relations_{timestamp}.csv')
    else:
        output_file = os.path.join(EXPORT_DIR, output_file)
    
    # Tulis data ke CSV
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Tulis header
            writer.writerow(['kata1', 'kata2', 'jenis_relasi', 'kekuatan'])
            # Tulis data
            writer.writerows(relations)
        
        print(f"Semua relasi tesaurus berhasil diekspor ke {output_file}. Total {len(relations)} relasi.")
        return output_file
    except Exception as e:
        print(f"Error saat mengekspor relasi tesaurus: {e}")
        return False
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Ekspor data dari database lexical dan tesaurus ke CSV")
    parser.add_argument('--type', choices=['lexical', 'synonyms', 'antonyms', 'all_relations'], default='lexical',
                       help='Jenis data yang akan diekspor')
    parser.add_argument('--output', type=str, help='Nama file output (opsional)')
    
    args = parser.parse_args()
    
    if args.type == 'lexical':
        export_lexical_data(args.output)
    elif args.type == 'synonyms':
        export_synonyms(args.output)
    elif args.type == 'antonyms':
        export_antonyms(args.output)
    elif args.type == 'all_relations':
        export_all_thesaurus_relations(args.output)

if __name__ == "__main__":
    main() 