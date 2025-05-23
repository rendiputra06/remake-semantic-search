"""
Modul untuk pencarian leksikal (lexical search) dalam Al-Quran
"""
import os
import re
import json
import pickle
from typing import List, Dict, Any, Tuple
from collections import defaultdict

class LexicalSearch:
    """
    Kelas untuk melakukan pencarian leksikal pada ayat-ayat Al-Quran
    """
    def __init__(self, index_path: str = '../database/lexical/inverted_index.pkl'):
        self.index_path = index_path
        self.inverted_index = defaultdict(list)  # kata -> [(id_ayat, posisi), ...]
        self.verse_data = {}  # Menyimpan data ayat untuk hasil
    
    def build_index(self, preprocessed_verses: Dict[str, Dict[str, Any]]) -> None:
        """
        Membangun indeks terbalik untuk pencarian leksikal
        """
        print("Building lexical search index...")
        
        # Simpan data ayat untuk referensi
        self.verse_data = preprocessed_verses
        
        # Bangun indeks terbalik
        for verse_id, verse_info in preprocessed_verses.items():
            if 'translation' in verse_info:
                # Gunakan teks terjemahan yang belum diproses
                text = verse_info['translation'].lower()
                
                # Indeks setiap kata dengan posisinya
                words = text.split()
                for position, word in enumerate(words):
                    # Hapus tanda baca
                    clean_word = re.sub(r'[^\w\s]', '', word)
                    if clean_word:
                        self.inverted_index[clean_word].append((verse_id, position))
        
        print(f"Lexical index built with {len(self.inverted_index)} unique terms")
        
        # Simpan indeks ke file
        self.save_index()
    
    def save_index(self) -> None:
        """
        Menyimpan indeks terbalik ke file
        """
        if not self.inverted_index:
            raise ValueError("Inverted index belum dibangun.")
        
        # Pastikan direktori ada
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Simpan indeks dan data ayat
        data_to_save = {
            'inverted_index': dict(self.inverted_index),
            'verse_data': self.verse_data
        }
        
        with open(self.index_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        
        print(f"Lexical index saved to {self.index_path}")
    
    def load_index(self) -> None:
        """
        Memuat indeks terbalik dari file
        """
        try:
            with open(self.index_path, 'rb') as f:
                data = pickle.load(f)
            
            self.inverted_index = defaultdict(list, data['inverted_index'])
            self.verse_data = data['verse_data']
            
            print(f"Loaded lexical index with {len(self.inverted_index)} terms")
        except Exception as e:
            print(f"Error loading lexical index: {e}")
            raise e
    
    def search(self, query: str, exact_match: bool = False, use_regex: bool = False, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian leksikal berdasarkan query
        
        Args:
            query (str): Teks yang dicari
            exact_match (bool): Jika True, cari frasa persis
            use_regex (bool): Jika True, interpretasikan query sebagai regex
            limit (int): Batasan jumlah hasil
            
        Returns:
            List[Dict[str, Any]]: Daftar hasil pencarian
        """
        if not self.inverted_index:
            try:
                self.load_index()
            except:
                raise ValueError("Inverted index belum dibangun dan tidak dapat dimuat.")
        
        results = []
        
        if use_regex:
            # Pencarian dengan regex
            results = self._search_regex(query, limit)
        elif exact_match:
            # Pencarian frasa persis
            results = self._search_exact_phrase(query, limit)
        else:
            # Pencarian sederhana (AND)
            results = self._search_keywords(query, limit)
        
        return results
    
    def _search_keywords(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        Mencari ayat yang mengandung semua kata kunci (operasi AND)
        """
        # Praproses query
        query = query.lower()
        query_words = [re.sub(r'[^\w\s]', '', word) for word in query.split()]
        query_words = [word for word in query_words if word]
        
        if not query_words:
            return []
        
        # Dapatkan semua verse_id yang mengandung kata pertama
        verse_ids = set(item[0] for item in self.inverted_index.get(query_words[0], []))
        
        # Interseksi dengan kata-kata lainnya (AND)
        for word in query_words[1:]:
            word_verse_ids = set(item[0] for item in self.inverted_index.get(word, []))
            verse_ids &= word_verse_ids
        
        # Format hasil
        results = []
        for verse_id in list(verse_ids)[:limit]:
            verse_info = self.verse_data[verse_id]
            results.append({
                'verse_id': verse_id,
                'surah_number': verse_info['surah_number'],
                'surah_name': verse_info['surah_name'],
                'ayat_number': verse_info['ayat_number'],
                'arabic': verse_info['arabic'],
                'translation': verse_info['translation'],
                'match_type': 'keywords'
            })
        
        return results
    
    def _search_exact_phrase(self, phrase: str, limit: int) -> List[Dict[str, Any]]:
        """
        Mencari frasa persis dalam ayat
        """
        # Praproses frasa
        phrase = phrase.lower()
        phrase_words = [re.sub(r'[^\w\s]', '', word) for word in phrase.split()]
        phrase_words = [word for word in phrase_words if word]
        
        if not phrase_words:
            return []
        
        # Dapatkan semua (verse_id, position) untuk kata pertama
        matches = self.inverted_index.get(phrase_words[0], [])
        
        # Verifikasi sequensial untuk kata-kata berikutnya
        results = []
        for verse_id, start_pos in matches:
            match_found = True
            
            # Verifikasi kata-kata berikutnya ada di posisi sekuensial
            for i, word in enumerate(phrase_words[1:], 1):
                next_pos = start_pos + i
                next_match = (verse_id, next_pos) in self.inverted_index.get(word, [])
                if not next_match:
                    match_found = False
                    break
            
            if match_found and verse_id not in [r['verse_id'] for r in results]:
                verse_info = self.verse_data[verse_id]
                results.append({
                    'verse_id': verse_id,
                    'surah_number': verse_info['surah_number'],
                    'surah_name': verse_info['surah_name'],
                    'ayat_number': verse_info['ayat_number'],
                    'arabic': verse_info['arabic'],
                    'translation': verse_info['translation'],
                    'match_type': 'exact_phrase'
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _search_regex(self, regex_pattern: str, limit: int) -> List[Dict[str, Any]]:
        """
        Mencari ayat dengan regex
        """
        try:
            pattern = re.compile(regex_pattern, re.IGNORECASE)
        except re.error:
            return []
        
        results = []
        checked_verses = set()
        
        # Periksa setiap ayat
        for verse_id, verse_info in self.verse_data.items():
            if verse_id in checked_verses:
                continue
                
            # Cari di teks terjemahan
            if pattern.search(verse_info['translation']):
                results.append({
                    'verse_id': verse_id,
                    'surah_number': verse_info['surah_number'],
                    'surah_name': verse_info['surah_name'],
                    'ayat_number': verse_info['ayat_number'],
                    'arabic': verse_info['arabic'],
                    'translation': verse_info['translation'],
                    'match_type': 'regex'
                })
                checked_verses.add(verse_id)
                
                if len(results) >= limit:
                    break
        
        return results 