import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.db import add_query, add_relevant_verse

ibadah_mapping = {
    "Shalat lima waktu": ["2:43", "4:103", "17:78"],
    "Puasa Ramadhan": ["2:183", "2:185"],
    "Zakat fitrah": ["2:110", "9:60"],
    "Haji ke Baitullah": ["2:196", "3:97"],
    "Tata cara wudhu": ["5:6"],
    "Doa setelah shalat": ["17:79", "3:191"],
    "Keutamaan shalat berjamaah": ["2:43", "9:18"],
    "Larangan meninggalkan shalat": ["19:59", "74:42-43"],
    "Niat puasa": ["2:187"],
    "Zakat mal": ["2:267", "9:103"],
    "Ibadah qurban": ["22:36", "37:107"],
    "Tata cara tayamum": ["4:43", "5:6"],
    "Shalat sunnah tahajud": ["17:79", "73:2"],
    "Shalat witir": ["2:238"],
    "Puasa sunnah Senin Kamis": ["33:35"],
    "Ibadah di bulan Ramadhan": ["2:185"],
    "Keutamaan membaca Al-Quran": ["2:121", "35:29"],
    "Adab berdoa": ["7:55", "40:60"],
    "Ibadah di masjid": ["9:18", "24:36"],
    "Shalat tarawih": ["73:20"]
}

def main():
    for query, ayat_list in ibadah_mapping.items():
        ok, query_id = add_query(query)
        if not ok:
            print(f"Gagal menambah query: {query}")
            continue
        for ayat_ref in ayat_list:
            # Support ayat range, e.g. 74:42-43
            if '-' in ayat_ref:
                surah, ayat_range = ayat_ref.split(':')
                start, end = map(int, ayat_range.split('-'))
                for ayat in range(start, end+1):
                    ok, msg = add_relevant_verse(query_id, f"{surah}:{ayat}")
                    if not ok:
                        print(f"  Gagal tambah ayat relevan: {surah}:{ayat} ({msg})")
            else:
                ok, msg = add_relevant_verse(query_id, ayat_ref)
                if not ok:
                    print(f"  Gagal tambah ayat relevan: {ayat_ref} ({msg})")
        print(f"Berhasil tambah query: {query}")

if __name__ == "__main__":
    main() 