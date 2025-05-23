#!/usr/bin/env python
"""
Script untuk mengayakan tesaurus dengan mencari relasi semantik dari wordlist
"""
import os
import sqlite3
import argparse
import json
from datetime import datetime
from collections import defaultdict
import re
import random

# Path ke database
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
LEXICAL_DB = os.path.join(DB_DIR, 'lexical.db')
WORDLIST_DIR = os.path.join(DB_DIR, 'wordlists')
THESAURUS_STATUS = os.path.join(DB_DIR, 'thesaurus_status.json')

def get_word_affinity(word1, word2, wordlists, min_score=0.5):
    """
    Menghitung skor afinitas antara dua kata berdasarkan keberadaan pada wordlist yang sama
    """
    if word1 == word2:
        return 0  # Kata yang sama tidak memiliki afinitas sinonim
    
    total_lists = len(wordlists)
    if total_lists == 0:
        return 0
    
    # Hitung berapa kali kedua kata muncul di wordlist yang sama
    common_lists = sum(1 for wordlist in wordlists if word1 in wordlist and word2 in wordlist)
    
    # Hitung skor afinitas (0-1)
    score = common_lists / total_lists
    
    # Hanya kembalikan skor jika di atas threshold
    return score if score >= min_score else 0

def get_similarity_by_pattern(word1, word2):
    """
    Menghitung kesamaan kata berdasarkan pola karakter
    """
    # Kasus khusus untuk kata pendek (kurang dari 4 karakter)
    if len(word1) < 4 or len(word2) < 4:
        return 0
    
    # Periksa apakah kata berbagi awalan atau akhiran yang signifikan
    prefix_len = 0
    while prefix_len < min(len(word1), len(word2)) and word1[prefix_len] == word2[prefix_len]:
        prefix_len += 1
    
    suffix_len = 0
    while (suffix_len < min(len(word1), len(word2)) and 
           word1[len(word1) - 1 - suffix_len] == word2[len(word2) - 1 - suffix_len]):
        suffix_len += 1
    
    # Hitung rasio kesamaan
    total_match = prefix_len + suffix_len
    max_len = max(len(word1), len(word2))
    
    # Jika lebih dari 70% karakter sama di awal atau akhir, mungkin terkait
    ratio = total_match / max_len
    
    return ratio if ratio >= 0.7 else 0

def find_word_relations(wordlist_file, relation_type='synonym', min_score=0.5, max_relations=5):
    """
    Mencari relasi kata potensial dari wordlist
    """
    if not os.path.exists(wordlist_file):
        print(f"File wordlist tidak ditemukan: {wordlist_file}")
        return []
    
    # Baca wordlist
    words = []
    with open(wordlist_file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                words.append(word)
    
    print(f"Memproses {len(words)} kata dari wordlist...")
    
    # Bagi wordlist menjadi beberapa grup untuk pemrosesan batch
    # Ini membantu mengurangi kompleksitas untuk kata yang banyak
    word_groups = defaultdict(list)
    
    # Kelompokkan kata berdasarkan huruf pertama untuk mempercepat pencarian
    for word in words:
        if word:
            first_letter = word[0].lower()
            word_groups[first_letter].append(word)
    
    # Cari relasi potensial
    relations = []
    
    # Jika mencari sinonim, gunakan kesamaan pola
    if relation_type == 'synonym':
        for group, group_words in word_groups.items():
            for i, word1 in enumerate(group_words):
                related_words = []
                
                # Hanya cek kata dalam grup yang sama dan grup yang berdekatan
                nearby_groups = [group]
                if ord(group) > ord('a'):
                    nearby_groups.append(chr(ord(group) - 1))
                if ord(group) < ord('z'):
                    nearby_groups.append(chr(ord(group) + 1))
                
                candidates = []
                for ng in nearby_groups:
                    for word2 in word_groups.get(ng, []):
                        if word1 != word2:
                            similarity = get_similarity_by_pattern(word1, word2)
                            if similarity >= min_score:
                                candidates.append((word2, similarity))
                
                # Ambil N kata dengan skor tertinggi
                candidates.sort(key=lambda x: x[1], reverse=True)
                for word2, score in candidates[:max_relations]:
                    relations.append((word1, word2, score))
    
    # Jika mencari antonim, gunakan pendekatan berbeda
    elif relation_type == 'antonym':
        # Untuk antonim, kita bisa menggunakan daftar awalan/akhiran yang umumnya mengindikasikan antonim
        antonym_prefixes = ['tidak ', 'non-', 'anti-', 'de-']
        
        for word in words:
            # Periksa apakah kata memiliki awalan yang mengindikasikan antonim
            for prefix in antonym_prefixes:
                if word.startswith(prefix):
                    base_word = word[len(prefix):]
                    if base_word in words:
                        relations.append((word, base_word, 0.9))
                else:
                    # Periksa jika ada versi dengan awalan
                    for prefix in antonym_prefixes:
                        antonym_candidate = prefix + word
                        if antonym_candidate in words:
                            relations.append((word, antonym_candidate, 0.9))
    
    # Jika mencari hiponim/hipernim, pendekatan lain diperlukan
    # Ini memerlukan pengetahuan tambahan atau model NLP yang lebih canggih
    
    print(f"Menemukan {len(relations)} kandidat relasi {relation_type}")
    return relations

def enrich_thesaurus_from_wordlist(wordlist_file, relation_type='synonym', min_score=0.5, max_relations=5):
    """
    Mengayakan database tesaurus dengan relasi dari wordlist
    """
    # Periksa apakah database ada
    if not os.path.exists(LEXICAL_DB):
        print("Database lexical belum diinisialisasi.")
        return False
    
    # Pastikan jenis relasi valid
    valid_relation_types = {
        'synonym': 'synonyms',
        'antonym': 'antonyms',
        'hyponym': 'hyponyms',
        'hypernym': 'hypernyms'
    }
    
    if relation_type not in valid_relation_types:
        print(f"Jenis relasi tidak valid: {relation_type}")
        return False
    
    # Tentukan tabel untuk relasi
    relation_table = valid_relation_types[relation_type]
    
    # Cari relasi dari wordlist
    relations = find_word_relations(wordlist_file, relation_type, min_score, max_relations)
    
    if not relations:
        print("Tidak ada relasi yang ditemukan untuk ditambahkan.")
        return False
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Masukkan relasi ke database
    added_count = 0
    
    # Simpan semua kata yang sudah ada di database
    cursor.execute("SELECT id, word FROM lexical")
    existing_words = {row[1]: row[0] for row in cursor.fetchall()}
    
    for word1, word2, score in relations:
        # Pastikan kedua kata ada di database lexical
        if word1 not in existing_words:
            cursor.execute(
                "INSERT INTO lexical (word, definition, example) VALUES (?, ?, ?)",
                (word1, "", "")
            )
            existing_words[word1] = cursor.lastrowid
        
        if word2 not in existing_words:
            cursor.execute(
                "INSERT INTO lexical (word, definition, example) VALUES (?, ?, ?)",
                (word2, "", "")
            )
            existing_words[word2] = cursor.lastrowid
        
        word1_id = existing_words[word1]
        word2_id = existing_words[word2]
        
        # Tentukan kolom untuk relasi berdasarkan jenis
        if relation_type == 'synonym':
            col1, col2 = 'word_id', 'synonym_id'
        elif relation_type == 'antonym':
            col1, col2 = 'word_id', 'antonym_id'
        elif relation_type == 'hyponym':
            col1, col2 = 'word_id', 'hyponym_id'
        elif relation_type == 'hypernym':
            col1, col2 = 'word_id', 'hypernym_id'
        
        try:
            # Cek apakah relasi sudah ada
            cursor.execute(
                f"SELECT COUNT(*) FROM {relation_table} WHERE {col1} = ? AND {col2} = ?",
                (word1_id, word2_id)
            )
            if cursor.fetchone()[0] == 0:
                # Tambahkan relasi baru
                if relation_type in ['synonym', 'antonym']:
                    cursor.execute(
                        f"INSERT INTO {relation_table} ({col1}, {col2}, strength) VALUES (?, ?, ?)",
                        (word1_id, word2_id, score)
                    )
                else:
                    cursor.execute(
                        f"INSERT INTO {relation_table} ({col1}, {col2}) VALUES (?, ?)",
                        (word1_id, word2_id)
                    )
                added_count += 1
        except sqlite3.IntegrityError:
            # Lewati jika ada konflik
            pass
    
    conn.commit()
    
    # Update status tesaurus
    update_thesaurus_status(conn)
    
    print(f"Berhasil menambahkan {added_count} relasi {relation_type} baru ke database tesaurus.")
    
    conn.close()
    return True

def update_thesaurus_status(conn):
    """Update status database tesaurus"""
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
    parser = argparse.ArgumentParser(description="Mengayakan tesaurus dengan relasi dari wordlist")
    parser.add_argument('--wordlist', type=str, required=True, help='Path ke file wordlist')
    parser.add_argument('--type', choices=['synonym', 'antonym', 'hyponym', 'hypernym'], default='synonym',
                       help='Jenis relasi yang akan dicari')
    parser.add_argument('--min-score', type=float, default=0.7, help='Skor minimum untuk relasi yang akan ditambahkan')
    parser.add_argument('--max-relations', type=int, default=5, help='Jumlah maksimum relasi per kata')
    
    args = parser.parse_args()
    
    enrich_thesaurus_from_wordlist(args.wordlist, args.type, args.min_score, args.max_relations)

if __name__ == "__main__":
    main() 