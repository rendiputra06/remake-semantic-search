# scripts/db/reset_relevant_verses.py
"""
Script untuk mereset (menghapus semua data) pada tabel relevant_verses.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'app.db')

def reset_relevant_verses():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM relevant_verses')
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='relevant_verses'")
        conn.commit()
        print('Tabel relevant_verses dan auto increment ID berhasil direset.')
    except Exception as e:
        print(f'Gagal mereset tabel relevant_verses: {e}')
    finally:
        conn.close()

if __name__ == "__main__":
    reset_relevant_verses()
