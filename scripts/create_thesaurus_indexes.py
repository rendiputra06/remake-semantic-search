#!/usr/bin/env python3
"""
Script untuk membuat database indexes untuk optimasi thesaurus
"""
import sqlite3
import os

def create_thesaurus_indexes():
    """Create indexes for thesaurus database optimization."""
    
    # Path ke database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'lexical.db')
    
    if not os.path.exists(db_path):
        print(f"Database tidak ditemukan: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Membuat indexes untuk optimasi thesaurus...")
        
        # Indexes untuk optimasi pencarian
        indexes = [
            # Lexical table indexes
            ("idx_lexical_word", "lexical", "word"),
            ("idx_lexical_word_lower", "lexical", "LOWER(word)"),
            
            # Synonyms table indexes
            ("idx_synonyms_word_id", "synonyms", "word_id"),
            ("idx_synonyms_synonym_id", "synonyms", "synonym_id"),
            ("idx_synonyms_strength", "synonyms", "strength"),
            
            # Antonyms table indexes
            ("idx_antonyms_word_id", "antonyms", "word_id"),
            ("idx_antonyms_antonym_id", "antonyms", "antonym_id"),
            ("idx_antonyms_strength", "antonyms", "strength"),
            
            # Hyponyms table indexes
            ("idx_hyponyms_word_id", "hyponyms", "word_id"),
            ("idx_hyponyms_hyponym_id", "hyponyms", "hyponym_id"),
            ("idx_hyponyms_strength", "hyponyms", "strength"),
            
            # Hypernyms table indexes
            ("idx_hypernyms_word_id", "hypernyms", "word_id"),
            ("idx_hypernyms_hypernym_id", "hypernyms", "hypernym_id"),
            ("idx_hypernyms_strength", "hypernyms", "strength"),
        ]
        
        for index_name, table_name, columns in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")
                print(f"✓ Index {index_name} berhasil dibuat")
            except sqlite3.Error as e:
                print(f"✗ Error membuat index {index_name}: {e}")
        
        # Commit perubahan
        conn.commit()
        conn.close()
        
        print("Semua indexes berhasil dibuat!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = create_thesaurus_indexes()
    if success:
        print("Database indexes berhasil dibuat!")
    else:
        print("Gagal membuat database indexes!") 