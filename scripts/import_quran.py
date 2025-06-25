#!/usr/bin/env python3
"""
Script untuk mengimpor data Quran dari file JSON ke database
"""
import os
import json
import sqlite3
from pathlib import Path

def get_db_connection():
    """Mendapatkan koneksi database"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def import_quran_data():
    """Mengimpor data Quran dari file JSON ke database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Path ke folder dataset/surah
    surah_dir = Path(__file__).parent.parent / 'dataset' / 'surah'
    
    print("Memulai import data Quran...")
    
    # Cek apakah sudah ada data
    cursor.execute('SELECT COUNT(*) FROM quran_surah')
    surah_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM quran_verses')
    verses_count = cursor.fetchone()[0]
    
    if surah_count > 0 or verses_count > 0:
        print(f"Database sudah berisi {surah_count} surah dan {verses_count} ayat")
        response = input("Lanjutkan import? (y/N): ")
        if response.lower() != 'y':
            print("Import dibatalkan")
            conn.close()
            return
    
    # Hapus data yang ada jika diminta
    cursor.execute('DELETE FROM quran_verses')
    cursor.execute('DELETE FROM quran_surah')
    
    total_surah = 0
    total_verses = 0
    
    # Iterasi semua file JSON
    for json_file in sorted(surah_dir.glob('*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ambil data surah (key pertama adalah nomor surah)
            surah_number = list(data.keys())[0]
            surah_data = data[surah_number]
            
            # Insert data surah
            cursor.execute('''
                INSERT INTO quran_surah 
                (surah_number, surah_name, surah_name_en, total_ayat, revelation_type, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                int(surah_number),
                surah_data['name'],
                surah_data.get('name_latin'),
                int(surah_data['number_of_ayah']),
                None,  # revelation_type
                None   # description
            ))
            
            total_surah += 1
            
            # Insert data ayat
            for verse_number, verse_text in surah_data['text'].items():
                # Ambil terjemahan jika ada
                translation = None
                if 'translations' in surah_data and 'id' in surah_data['translations']:
                    translation = surah_data['translations']['id']['text'].get(verse_number)
                
                cursor.execute('''
                    INSERT INTO quran_verses 
                    (surah_id, surah_name, verse_number, verse_text, verse_translation)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    int(surah_number),
                    surah_data['name'],
                    int(verse_number),
                    verse_text,
                    translation
                ))
                
                total_verses += 1
            
            print(f"✓ Surah {surah_number}: {surah_data['name']} ({surah_data['number_of_ayah']} ayat)")
            
        except Exception as e:
            print(f"✗ Error pada file {json_file.name}: {e}")
            continue
    
    # Commit perubahan
    conn.commit()
    conn.close()
    
    print(f"\nImport selesai!")
    print(f"Total surah: {total_surah}")
    print(f"Total ayat: {total_verses}")

def verify_import():
    """Verifikasi data yang telah diimport"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\nVerifikasi data:")
    
    # Cek jumlah surah
    cursor.execute('SELECT COUNT(*) FROM quran_surah')
    surah_count = cursor.fetchone()[0]
    print(f"Jumlah surah di database: {surah_count}")
    
    # Cek jumlah ayat
    cursor.execute('SELECT COUNT(*) FROM quran_verses')
    verses_count = cursor.fetchone()[0]
    print(f"Jumlah ayat di database: {verses_count}")
    
    # Cek sample data
    cursor.execute('SELECT * FROM quran_surah ORDER BY surah_number LIMIT 3')
    sample_surah = cursor.fetchall()
    print("\nSample surah:")
    for surah in sample_surah:
        print(f"  {surah['surah_number']}: {surah['surah_name']} ({surah['surah_name_en']})")
    
    cursor.execute('SELECT * FROM quran_verses WHERE surah_id = 1 ORDER BY verse_number LIMIT 3')
    sample_verses = cursor.fetchall()
    print("\nSample ayat (Surah 1):")
    for verse in sample_verses:
        print(f"  Ayat {verse['verse_number']}: {verse['verse_text'][:50]}...")
    
    conn.close()

if __name__ == '__main__':
    import_quran_data()
    verify_import() 