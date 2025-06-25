import sqlite3

def check_quran_data():
    conn = sqlite3.connect('database/app.db')
    cursor = conn.cursor()
    
    # Check quran_index data
    cursor.execute('SELECT COUNT(*) FROM quran_index')
    index_count = cursor.fetchone()[0]
    print(f'Total quran_index records: {index_count}')
    
    # Check sample data
    cursor.execute('SELECT id, title, level, parent_id, list_ayat FROM quran_index LIMIT 5')
    rows = cursor.fetchall()
    print('\nSample quran_index data:')
    for row in rows:
        ayat_preview = row[4][:50] + '...' if row[4] and len(row[4]) > 50 else (row[4] if row[4] else 'None')
        print(f'ID: {row[0]}, Title: {row[1]}, Level: {row[2]}, Parent: {row[3]}, Ayat: {ayat_preview}')
    
    # Check quran_verses data
    cursor.execute('SELECT COUNT(*) FROM quran_verses')
    verses_count = cursor.fetchone()[0]
    print(f'\nTotal quran_verses records: {verses_count}')
    
    # Check quran_surah data
    cursor.execute('SELECT COUNT(*) FROM quran_surah')
    surah_count = cursor.fetchone()[0]
    print(f'Total quran_surah records: {surah_count}')
    
    # Check indexes with ayat
    cursor.execute('SELECT COUNT(*) FROM quran_index WHERE list_ayat IS NOT NULL AND list_ayat != ""')
    indexes_with_ayat = cursor.fetchone()[0]
    print(f'Indexes with ayat data: {indexes_with_ayat}')
    
    conn.close()

if __name__ == '__main__':
    check_quran_data() 