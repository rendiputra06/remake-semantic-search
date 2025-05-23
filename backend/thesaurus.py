"""
Modul untuk tesaurus sinonim Bahasa Indonesia
"""
import os
import json
import pickle
from typing import List, Dict, Set, Any
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

class IndonesianThesaurus:
    """
    Kelas untuk mengelola tesaurus sinonim Bahasa Indonesia
    """
    def __init__(self, thesaurus_path: str = '../database/thesaurus/id_thesaurus.pkl', 
                 custom_thesaurus_path: str = '../database/thesaurus/custom_thesaurus.json'):
        self.thesaurus_path = thesaurus_path
        self.custom_thesaurus_path = custom_thesaurus_path
        self.thesaurus = {}  # kata -> [sinonim1, sinonim2, ...]
        self.stemmer = StemmerFactory().create_stemmer()
        
        # Inisialisasi tesaurus dasar
        self._initialize_base_thesaurus()
        
        # Muat tesaurus kustom jika ada
        self._load_custom_thesaurus()
    
    def _initialize_base_thesaurus(self):
        """
        Inisialisasi tesaurus dasar dari file pickle atau buat default
        """
        try:
            # Coba muat dari pickle yang sudah ada
            if os.path.exists(self.thesaurus_path):
                with open(self.thesaurus_path, 'rb') as f:
                    self.thesaurus = pickle.load(f)
                print(f"Loaded thesaurus with {len(self.thesaurus)} entries from {self.thesaurus_path}")
                return
        except Exception as e:
            print(f"Error loading thesaurus: {e}")
        
        # Jika gagal atau file tidak ada, buat tesaurus dasar statis
        print("Building base thesaurus...")
        
        # Kamus sinonim dasar bahasa Indonesia
        base_thesaurus = {
            # Dasar
            "besar": ["agung", "akbar", "raya", "luas", "tinggi", "hebat"],
            "kecil": ["mungil", "mini", "sedikit", "remeh", "sepele", "kerdil"],
            "bagus": ["baik", "indah", "cantik", "elok", "menawan", "rupawan"],
            "buruk": ["jelek", "rusak", "busuk", "jahat", "keji", "kotor"],
            
            # Kata umum
            "cepat": ["lekas", "segera", "kilat", "ekspres", "tangkas"],
            "lambat": ["pelan", "perlahan", "lamban", "malas"],
            "senang": ["gembira", "bahagia", "ceria", "riang", "suka"],
            "sedih": ["pilu", "murung", "duka", "susah", "merana"],
            "marah": ["kesal", "geram", "murka", "berang", "gusar"],
            "takut": ["cemas", "khawatir", "gentar", "ciut", "panik"],
            
            # Keagamaan
            "doa": ["permohonan", "harapan", "permintaan", "pinta"],
            "syukur": ["terima kasih", "berterima kasih", "ungkapan terima kasih"],
            "iman": ["percaya", "yakin", "kepercayaan", "keyakinan"],
            "ibadah": ["pemujaan", "penyembahan", "ritual", "upacara"],
            "pahala": ["ganjaran", "balasan", "imbalan", "upah"],
            "surga": ["firdaus", "syurga", "kayangan"],
            "neraka": ["jahanam", "api neraka", "lembah hitam"],
            "dosa": ["kesalahan", "pelanggaran", "maksiat"],
            "taubat": ["ampun", "maaf", "pengampunan", "penyesalan"],
            "sabar": ["tabah", "tenang", "tekun", "tahan"],
            
            # Kata kerja
            "pergi": ["berangkat", "berjalan", "berlalu"],
            "datang": ["tiba", "hadir", "muncul"],
            "buat": ["bikin", "ciptakan", "hasilkan"],
            "lihat": ["pandang", "amati", "perhatikan", "tatap"],
            "dengar": ["simak", "menguping"],
            
            # Kata sifat
            "baik": ["bagus", "hebat", "cantik", "indah"],
            "jahat": ["buruk", "jelek", "kejam", "keji"],
            "tinggi": ["menjulang", "megah"],
            "rendah": ["pendek", "mungil"],
            
            # Kata benda
            "rumah": ["kediaman", "tempat tinggal", "hunian"],
            "mobil": ["kendaraan", "kereta", "otomobil"],
            "makanan": ["santapan", "hidangan", "sajian"],
            "air": ["cairan", "minuman"],
            "buku": ["kitab", "bacaan", "majalah"],
            
            # Pembelajaran
            "belajar": ["pelajari", "mengkaji", "meneliti", "mendalami"],
            "mengajar": ["mendidik", "membimbing", "melatih"],
            "ilmu": ["pengetahuan", "wawasan", "pelajaran", "edukasi"],
            "pikir": ["renungkan", "pertimbangkan", "merenung"],
            "pintar": ["cerdas", "pandai", "jenius", "bijak"]
        }
        
        # Gabungkan dengan thesaurus dasar
        self.thesaurus = base_thesaurus
        
        # Simpan ke pickle untuk penggunaan berikutnya
        os.makedirs(os.path.dirname(self.thesaurus_path), exist_ok=True)
        with open(self.thesaurus_path, 'wb') as f:
            pickle.dump(self.thesaurus, f)
        
        print(f"Created and saved base thesaurus with {len(self.thesaurus)} entries")
    
    def _load_custom_thesaurus(self):
        """
        Muat tesaurus kustom dari file JSON
        """
        try:
            if os.path.exists(self.custom_thesaurus_path):
                with open(self.custom_thesaurus_path, 'r', encoding='utf-8') as f:
                    custom_thesaurus = json.load(f)
                
                # Gabungkan dengan tesaurus dasar
                for word, synonyms in custom_thesaurus.items():
                    if word in self.thesaurus:
                        # Gabungkan dengan sinonim yang sudah ada
                        existing = set(self.thesaurus[word])
                        new = set(synonyms)
                        self.thesaurus[word] = list(existing.union(new))
                    else:
                        # Tambahkan entri baru
                        self.thesaurus[word] = synonyms
                
                print(f"Loaded custom thesaurus from {self.custom_thesaurus_path}")
        except Exception as e:
            print(f"Error loading custom thesaurus: {e}")
    
    def get_synonyms(self, word: str) -> List[str]:
        """
        Mendapatkan daftar sinonim untuk suatu kata
        """
        word = word.lower()
        
        # Coba dapatkan sinonim untuk kata asli
        synonyms = set(self.thesaurus.get(word, []))
        
        # Jika tidak ditemukan, coba dengan kata dasar (stemming)
        if not synonyms:
            stemmed_word = self.stemmer.stem(word)
            if stemmed_word != word:
                synonyms = set(self.thesaurus.get(stemmed_word, []))
        
        return list(synonyms)
    
    def add_synonym(self, word: str, synonym: str) -> bool:
        """
        Menambahkan sinonim ke tesaurus kustom
        """
        word = word.lower()
        synonym = synonym.lower()
        
        # Muat tesaurus kustom yang ada
        custom_thesaurus = {}
        if os.path.exists(self.custom_thesaurus_path):
            try:
                with open(self.custom_thesaurus_path, 'r', encoding='utf-8') as f:
                    custom_thesaurus = json.load(f)
            except:
                custom_thesaurus = {}
        
        # Tambahkan sinonim
        if word in custom_thesaurus:
            if synonym not in custom_thesaurus[word]:
                custom_thesaurus[word].append(synonym)
        else:
            custom_thesaurus[word] = [synonym]
        
        # Simpan kembali
        os.makedirs(os.path.dirname(self.custom_thesaurus_path), exist_ok=True)
        with open(self.custom_thesaurus_path, 'w', encoding='utf-8') as f:
            json.dump(custom_thesaurus, f, ensure_ascii=False, indent=2)
        
        # Perbarui tesaurus internal
        if word in self.thesaurus:
            if synonym not in self.thesaurus[word]:
                self.thesaurus[word].append(synonym)
        else:
            self.thesaurus[word] = [synonym]
        
        return True
    
    def expand_query(self, query: str) -> List[str]:
        """
        Memperluas query dengan sinonim untuk setiap kata
        """
        words = query.lower().split()
        expanded_queries = [query]  # Selalu sertakan query asli
        
        # Jika query hanya satu kata, tambahkan semua sinonimnya
        if len(words) == 1:
            synonyms = self.get_synonyms(words[0])
            expanded_queries.extend(synonyms)
        # Jika query lebih dari satu kata, buat kombinasi dengan mengganti satu kata dengan sinonimnya
        else:
            for i, word in enumerate(words):
                synonyms = self.get_synonyms(word)
                for synonym in synonyms:
                    new_query = words.copy()
                    new_query[i] = synonym
                    expanded_queries.append(" ".join(new_query))
        
        # Hapus duplikat
        return list(set(expanded_queries))
    
    def create_default_thesaurus(self) -> None:
        """
        Buat tesaurus default dengan istilah umum dalam konteks Al-Quran
        """
        quran_thesaurus = {
            "allah": ["tuhan", "ilahi", "yang maha kuasa", "yang maha esa", "pencipta", "khalik", "rabb", "yang maha pengasih", "yang maha penyayang"],
            "tuhan": ["allah", "yang maha kuasa", "sang pencipta", "ilahi", "yang maha esa", "rabb"],
            "rasul": ["nabi", "utusan", "pesuruh allah", "muhammad", "rasulullah", "duta", "kurir"],
            "nabi": ["rasul", "utusan", "pesuruh allah", "muhammad", "rasulullah", "duta"],
            "kitab": ["quran", "al-quran", "wahyu", "firman", "kitabullah", "bacaan", "suci"],
            "quran": ["al-quran", "kitab", "firman", "wahyu", "kitabullah", "bacaan", "suci", "al-furqan"],
            "dosa": ["kesalahan", "keburukan", "maksiat", "pelanggaran", "salah", "khilaf", "amalan buruk"],
            "pahala": ["ganjaran", "balasan baik", "imbalan", "hadiah", "upah"],
            "surga": ["jannah", "firdaus", "kebahagiaan abadi", "syurga", "taman surga", "kehidupan kekal"],
            "neraka": ["jahannam", "azab", "siksa", "api neraka", "tempat siksaan"],
            "shalat": ["sembahyang", "ibadah", "doa", "solat", "rukun islam", "salat"],
            "puasa": ["shaum", "menahan diri", "berpantang", "rukun islam", "sawm"],
            "zakat": ["sedekah", "infaq", "pemberian", "amal", "rukun islam"],
            "haji": ["ibadah haji", "ziarah suci", "rukun islam", "ibadah ke baitullah", "umrah"],
            "takwa": ["ketakwaan", "keimanan", "ketaatan", "takut kepada allah", "patuh", "penyerahan diri"],
            "iman": ["keyakinan", "kepercayaan", "keimanan", "percaya", "yakin", "taqwa"],
            "islam": ["agama islam", "keislaman", "ketundukan", "kepasrahan", "agama", "berserah diri"],
            "akhirat": ["kehidupan setelah mati", "alam baka", "yaumil akhir", "hari kemudian", "dunia setelah kematian"],
            "bumi": ["dunia", "alam", "ciptaan", "darat", "ardh", "tanah"],
            "langit": ["angkasa", "semesta", "cakrawala", "samawi", "alam atas"],
            "hidayah": ["petunjuk", "bimbingan", "arahan", "pimpinan", "tuntunan", "guidance"],
            "rahmat": ["kasih sayang", "belas kasih", "kebaikan", "berkah", "anugrah", "karunia"],
            "sabar": ["tabah", "tahan uji", "tekun", "tenang", "tidak mudah marah", "lapang dada"],
            "syukur": ["berterima kasih", "mensyukuri", "bersyukur", "terima kasih", "apresiasi", "ungkapan terima kasih"],
            "taubat": ["ampunan", "maaf", "kembali", "bertobat", "penyesalan", "pengampunan", "istighfar"],
            "setan": ["iblis", "syaitan", "jin", "pembisik", "musuh", "penggoda"],
            "malaikat": ["bidadari", "makhluk suci", "makhluk cahaya", "makhluk allah", "utusan"],
            "sedekah": ["infaq", "zakat", "sumbangan", "pemberian", "amal", "donasi"],
            "ikhlas": ["tulus", "murni", "tanpa pamrih", "rela", "tanpa keinginan imbalan"],
            "adil": ["bijaksana", "seimbang", "rata", "tidak berat sebelah", "fair", "merata"],
            "benar": ["betul", "jujur", "tepat", "nyata", "faktual", "tidak bohong"],
            "bohong": ["dusta", "tipu", "tidak jujur", "kebohongan", "berbohong", "tidak benar"],
            "halal": ["diizinkan", "diperbolehkan", "sah", "legal", "boleh", "tidak haram"],
            "haram": ["terlarang", "tidak boleh", "dilarang", "tidak sah", "tidak halal"]
        }
        
        # Simpan ke file kustom
        os.makedirs(os.path.dirname(self.custom_thesaurus_path), exist_ok=True)
        with open(self.custom_thesaurus_path, 'w', encoding='utf-8') as f:
            json.dump(quran_thesaurus, f, ensure_ascii=False, indent=2)
        
        # Perbarui tesaurus internal
        for word, synonyms in quran_thesaurus.items():
            self.thesaurus[word] = synonyms
        
        print(f"Created default Quran thesaurus with {len(quran_thesaurus)} entries") 