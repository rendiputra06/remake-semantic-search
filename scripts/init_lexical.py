#!/usr/bin/env python
"""
Script untuk menginisialisasi database leksikal dan tesaurus
"""
import os
import json
import sqlite3
import argparse
from datetime import datetime

# Path ke database
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
LEXICAL_DB = os.path.join(DB_DIR, 'lexical.db')
LEXICAL_STATUS = os.path.join(DB_DIR, 'lexical_status.json')
THESAURUS_STATUS = os.path.join(DB_DIR, 'thesaurus_status.json')

def init_lexical_db():
    """Inisialisasi database leksikal"""
    # Pastikan direktori database ada
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Hapus database lama jika ada
    if os.path.exists(LEXICAL_DB):
        os.remove(LEXICAL_DB)
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Buat tabel leksikal
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lexical (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        definition TEXT,
        example TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(word)
    )
    ''')
    
    # Buat indeks
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON lexical(word)')
    
    # Commit perubahan dan tutup koneksi
    conn.commit()
    conn.close()
    
    # Update status
    update_lexical_status(0)
    
    print("Database leksikal berhasil diinisialisasi.")

def init_thesaurus_db():
    """Inisialisasi database tesaurus"""
    # Pastikan direktori database ada
    os.makedirs(DB_DIR, exist_ok=True)
    
    # Pastikan database lexical ada
    if not os.path.exists(LEXICAL_DB):
        print("Database lexical belum diinisialisasi. Menginisialisasi...")
        init_lexical_db()
    
    # Buat koneksi ke database
    conn = sqlite3.connect(LEXICAL_DB)
    cursor = conn.cursor()
    
    # Buat tabel untuk sinonim
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS synonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        synonym_id INTEGER NOT NULL,
        strength REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES lexical(id),
        FOREIGN KEY (synonym_id) REFERENCES lexical(id),
        UNIQUE(word_id, synonym_id)
    )
    ''')
    
    # Buat tabel untuk antonim
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS antonyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        antonym_id INTEGER NOT NULL,
        strength REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES lexical(id),
        FOREIGN KEY (antonym_id) REFERENCES lexical(id),
        UNIQUE(word_id, antonym_id)
    )
    ''')
    
    # Buat tabel untuk hiponim (kata yang lebih spesifik)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hyponyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        hyponym_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES lexical(id),
        FOREIGN KEY (hyponym_id) REFERENCES lexical(id),
        UNIQUE(word_id, hyponym_id)
    )
    ''')
    
    # Buat tabel untuk hipernim (kata yang lebih umum)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hypernyms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        hypernym_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES lexical(id),
        FOREIGN KEY (hypernym_id) REFERENCES lexical(id),
        UNIQUE(word_id, hypernym_id)
    )
    ''')
    
    # Buat indeks
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_syn_word ON synonyms(word_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_syn_synonym ON synonyms(synonym_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ant_word ON antonyms(word_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ant_antonym ON antonyms(antonym_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hypo_word ON hyponyms(word_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hypo_hyponym ON hyponyms(hyponym_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hyper_word ON hypernyms(word_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hyper_hypernym ON hypernyms(hypernym_id)')
    
    # Commit perubahan dan tutup koneksi
    conn.commit()
    conn.close()
    
    # Update status
    update_thesaurus_status(0, 0)
    
    print("Database tesaurus berhasil diinisialisasi.")

def update_lexical_status(entry_count):
    """Update status database leksikal"""
    status = {
        'initialized': True,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'entry_count': entry_count
    }
    
    with open(LEXICAL_STATUS, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def update_thesaurus_status(word_count, relation_count):
    """Update status database tesaurus"""
    status = {
        'initialized': True,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'word_count': word_count,
        'relation_count': relation_count
    }
    
    with open(THESAURUS_STATUS, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Inisialisasi database leksikal dan tesaurus")
    parser.add_argument('--component', choices=['lexical', 'thesaurus', 'all'], default='all',
                        help='Komponen yang akan diinisialisasi')
    
    args = parser.parse_args()
    
    if args.component in ['lexical', 'all']:
        init_lexical_db()
    
    if args.component in ['thesaurus', 'all']:
        init_thesaurus_db()

if __name__ == "__main__":
    main() 