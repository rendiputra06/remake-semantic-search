import sqlite3
import json
import re

def clean_ayat_ref(ayat_ref):
    # Hilangkan awalan 'Qs.', 'QS.', 'qs.', dan spasi
    cleaned = re.sub(r'^(Qs\.|QS\.|qs\.|\s+)', '', ayat_ref)
    # Hilangkan awalan 'Q.S.' juga jika ada
    cleaned = re.sub(r'^(Q\.S\.|q\.s\.|Q\.s\.|q\.S\.)', '', cleaned)
    # Hilangkan spasi di awal dan akhir
    cleaned = cleaned.strip()
    # Hilangkan spasi di antara surah dan ayat (misal '2 : 255' -> '2:255')
    cleaned = re.sub(r'\s*:\s*', ':', cleaned)
    return cleaned

def clean_all_quran_index_ayat(db_path='database/app.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, list_ayat FROM quran_index WHERE list_ayat IS NOT NULL AND list_ayat != ""')
    rows = cursor.fetchall()
    updated = 0
    for idx, list_ayat_json in rows:
        try:
            ayat_list = json.loads(list_ayat_json)
            cleaned_list = [clean_ayat_ref(a) for a in ayat_list]
            # Hanya update jika ada perubahan
            if ayat_list != cleaned_list:
                cursor.execute('UPDATE quran_index SET list_ayat = ? WHERE id = ?', (json.dumps(cleaned_list), idx))
                updated += 1
        except Exception as e:
            print(f"Gagal membersihkan index id={idx}: {e}")
    conn.commit()
    conn.close()
    print(f"Selesai membersihkan. {updated} index diperbarui.")

if __name__ == '__main__':
    clean_all_quran_index_ayat() 