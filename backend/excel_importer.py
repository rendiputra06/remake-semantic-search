"""
Modul untuk mengimpor data dari file Excel ke dalam database
"""
import pandas as pd
import json
import datetime
import os
import sqlite3
from backend.db import get_db_connection, delete_quran_index

def excel_to_hierarchy_db(file_path, sheet_name, parent_main_id=None):
    """
    Fungsi untuk memproses file Excel dan mengimpornya ke dalam database index Al-Quran
    dengan menyimpan daftar ayat dalam format JSON di field list_ayat.
    Jika parent_main_id diberikan, semua sub-indeks dari parent tersebut akan dihapus terlebih dahulu.
    
    Args:
        file_path (str): Path file Excel
        sheet_name (str): Nama sheet yang akan diproses
        parent_main_id (int, optional): ID parent index jika ada. Default: None
        
    Returns:
        tuple: (success, message)
    """
    conn = None
    
    try:
        # Buka koneksi database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jika parent_main_id diberikan, hapus semua sub-indeks terlebih dahulu
        if parent_main_id is not None:
            # Dapatkan semua sub-indeks langsung dari parent
            cursor.execute('SELECT id FROM quran_index WHERE parent_id = ?', (parent_main_id,))
            sub_indexes = cursor.fetchall()
            
            # Hapus setiap sub-indeks (fungsi delete_quran_index akan menghapus secara rekursif)
            for sub_index in sub_indexes:
                success, message = delete_quran_index(sub_index['id'])
                if not success:
                    return False, f"Gagal menghapus sub-indeks: {message}"
        
        # Baca file Excel
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Tutup dan lepaskan file untuk memastikan tidak dikunci
        excel_file = pd.ExcelFile(file_path)
        excel_file.close()
        del excel_file
        
        # Membuat sub-dataframe yang dimulai dari kolom B dan melewati dua baris pertama
        if df.shape[0] > 2:  # Pastikan memiliki minimal 3 baris
            df = df.iloc[2:, 1:]
        else:
            return False, "Format file Excel tidak valid: minimal harus memiliki 3 baris"
        
        # Drop baris yang kosong (semua kolom NaN)
        df = df.dropna(how='all')
        
        # Reset indeks setelah operasi drop
        df = df.reset_index(drop=True)
        
        # Tampung data indeks dan ayat
        inserted_indexes = 0
        inserted_ayats = 0
        
        # Periksa level parent jika ada
        parent_level = 0
        if parent_main_id is not None:
            cursor.execute('SELECT level FROM quran_index WHERE id = ?', (parent_main_id,))
            parent_data = cursor.fetchone()
            if parent_data:
                parent_level = parent_data['level']
        
        # Fungsi untuk mengekstrak ayat dari baris
        def extract_ayats(row):
            ayat_list = []
            # Mulai dari kolom ke-6 (indeks 5) atau yang tersedia
            start_col = min(5, len(row) - 1)
            for col in range(start_col, len(row)):
                if pd.notna(row[col]):
                    ayat_text = str(row[col]).strip()
                    if ayat_text:
                        ayat_list.append(ayat_text)
            return ayat_list if ayat_list else None
        
        # Inisialisasi struktur hierarki
        hierarchy = {}
        
        # Pertama, buat struktur hierarki dari DataFrame
        for row_idx in range(len(df)):
            # Tentukan level tertinggi yang memiliki nilai pada baris ini
            current_level = None
            for col_idx in range(df.shape[1]):
                if pd.notna(df.iloc[row_idx, col_idx]):
                    current_level = col_idx
                    break
            
            if current_level is None:
                continue  # Lewati baris kosong
            
            # Simpan data baris dalam struktur
            hierarchy[row_idx] = {
                'level': current_level,
                'title': str(df.iloc[row_idx, current_level]).strip(),
                'ayats': extract_ayats(df.iloc[row_idx]),
                'parent_row': None,
                'children': []
            }
            
            # Cari parent untuk baris ini
            if current_level > 0:
                # Cari baris sebelumnya dengan level lebih rendah (yang akan menjadi parent)
                for prev_row in range(row_idx - 1, -1, -1):
                    if prev_row in hierarchy and hierarchy[prev_row]['level'] < current_level:
                        hierarchy[row_idx]['parent_row'] = prev_row
                        hierarchy[prev_row]['children'].append(row_idx)
                        break
        
        # Fungsi untuk menyisipkan node ke database
        def insert_node(row_idx, parent_db_id=None):
            nonlocal inserted_indexes, inserted_ayats
            
            node = hierarchy[row_idx]
            absolute_level = parent_level + node['level'] + 1
            now = datetime.datetime.now().isoformat()
            
            # Siapkan data JSON ayat
            ayat_json = json.dumps(node['ayats']) if node['ayats'] else None
            
            # Insert node ke database
            cursor.execute('''
            INSERT INTO quran_index (
                title, 
                description, 
                parent_id, 
                level, 
                sort_order, 
                list_ayat, 
                created_at, 
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node['title'],
                '',
                parent_db_id if parent_db_id is not None else parent_main_id,
                absolute_level,
                0,
                ayat_json,
                now,
                now
            ))
            
            node_id = cursor.lastrowid
            inserted_indexes += 1
            
            # Insert ayat ke database jika ada
            if node['ayats']:
                for ayat_text in node['ayats']:
                    # Format ayat: Surah:Ayat
                    parts = ayat_text.split(':')
                    if len(parts) == 2:
                        try:
                            surah = int(parts[0].strip())
                            ayat_num = int(parts[1].strip())
                            
                            cursor.execute('''
                            INSERT INTO quran_ayat (
                                index_id, 
                                surah, 
                                ayat, 
                                text, 
                                translation, 
                                created_at, 
                                updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                node_id,
                                surah,
                                ayat_num,
                                f'Surah {surah}:{ayat_num}',
                                'Perlu dilengkapi',
                                now,
                                now
                            ))
                            inserted_ayats += 1
                        except ValueError:
                            # Abaikan jika format tidak valid
                            pass
            
            # Proses semua anak node
            for child_row in node['children']:
                insert_node(child_row, node_id)
            
            return node_id
        
        # Mulai proses penyisipan dari node-node root (level 0)
        root_nodes = [row_idx for row_idx in hierarchy if hierarchy[row_idx]['parent_row'] is None]
        for root_idx in root_nodes:
            insert_node(root_idx)
        
        # Commit perubahan
        conn.commit()
        
        return True, f"Berhasil mengimpor {inserted_indexes} indeks dan {inserted_ayats} ayat dari file Excel"
    
    except Exception as e:
        # Jika terjadi error, rollback
        if conn:
            conn.rollback()
        return False, f"Error saat memproses file Excel: {str(e)}"
    finally:
        # Pastikan koneksi ditutup
        if conn:
            conn.close()

def get_excel_sheets(file_path):
    """
    Mendapatkan daftar sheet dari file Excel
    
    Args:
        file_path (str): Path file Excel
        
    Returns:
        tuple: (success, sheets atau error message)
    """
    try:
        # Baca daftar sheet dengan aman
        excel = pd.ExcelFile(file_path)
        sheets = excel.sheet_names
        excel.close()
        
        return True, sheets
    except Exception as e:
        return False, f"Error saat membaca file Excel: {str(e)}"

if __name__ == "__main__":
    # Contoh penggunaan
    print("Modul impor Excel untuk indeks Al-Quran") 