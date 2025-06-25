#!/usr/bin/env python3
"""
Script untuk verifikasi data ontologi di database
"""

import os
import sys
import json
import sqlite3

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db_connection

def load_json_ontology():
    """Load ontology from JSON file"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ontology', 'ontology.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('concepts', [])
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return []

def load_db_ontology():
    """Load ontology from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ontology_concepts')
        rows = cursor.fetchall()
        
        concepts = []
        for row in rows:
            concept = {
                'id': row['id'],
                'label': row['label'],
                'synonyms': json.loads(row['synonyms']) if row['synonyms'] else [],
                'broader': json.loads(row['broader']) if row['broader'] else [],
                'narrower': json.loads(row['narrower']) if row['narrower'] else [],
                'related': json.loads(row['related']) if row['related'] else [],
                'verses': json.loads(row['verses']) if row['verses'] else []
            }
            concepts.append(concept)
        
        conn.close()
        return concepts
    except Exception as e:
        print(f"❌ Error loading from database: {e}")
        return []

def compare_concepts(json_concepts, db_concepts):
    """Compare concepts between JSON and database"""
    print(f"\n📊 Perbandingan Data:")
    print(f"JSON: {len(json_concepts)} konsep")
    print(f"Database: {len(db_concepts)} konsep")
    
    # Check for missing concepts
    json_ids = {c['id'] for c in json_concepts}
    db_ids = {c['id'] for c in db_concepts}
    
    missing_in_db = json_ids - db_ids
    missing_in_json = db_ids - json_ids
    
    if missing_in_db:
        print(f"\n⚠️  Konsep yang hilang di database: {len(missing_in_db)}")
        for cid in sorted(missing_in_db):
            print(f"  - {cid}")
    
    if missing_in_json:
        print(f"\n⚠️  Konsep yang hilang di JSON: {len(missing_in_json)}")
        for cid in sorted(missing_in_json):
            print(f"  - {cid}")
    
    # Check for differences in existing concepts
    differences = 0
    for json_concept in json_concepts:
        db_concept = next((c for c in db_concepts if c['id'] == json_concept['id']), None)
        if db_concept:
            if json_concept != db_concept:
                differences += 1
                print(f"\n🔍 Perbedaan pada konsep '{json_concept['id']}':")
                for key in ['label', 'synonyms', 'broader', 'narrower', 'related', 'verses']:
                    if json_concept.get(key) != db_concept.get(key):
                        print(f"  {key}:")
                        print(f"    JSON: {json_concept.get(key)}")
                        print(f"    DB:   {db_concept.get(key)}")
    
    if differences == 0 and not missing_in_db and not missing_in_json:
        print("\n✅ Data JSON dan database identik!")
        return True
    else:
        print(f"\n❌ Ditemukan {differences} konsep dengan perbedaan data")
        return False

def analyze_database_structure():
    """Analyze database structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(ontology_concepts)")
        columns = cursor.fetchall()
        
        print("\n🏗️  Struktur Tabel ontology_concepts:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
        
        # Check indexes
        cursor.execute("PRAGMA index_list(ontology_concepts)")
        indexes = cursor.fetchall()
        
        if indexes:
            print("\n📇 Indexes:")
            for idx in indexes:
                print(f"  - {idx[1]}")
        
        # Check table size
        cursor.execute("SELECT COUNT(*) as count FROM ontology_concepts")
        count = cursor.fetchone()['count']
        print(f"\n📊 Total records: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

def main():
    """Main function"""
    print("🔍 Verifikasi Data Ontologi Database...")
    
    # Load data
    print("\n📖 Loading data...")
    json_concepts = load_json_ontology()
    db_concepts = load_db_ontology()
    
    if not json_concepts:
        print("❌ Tidak bisa load data JSON")
        return False
    
    if not db_concepts:
        print("❌ Tidak bisa load data database")
        return False
    
    # Analyze database structure
    analyze_database_structure()
    
    # Compare data
    is_identical = compare_concepts(json_concepts, db_concepts)
    
    # Sample data
    print(f"\n📋 Sample Data (5 pertama):")
    for i, concept in enumerate(db_concepts[:5]):
        print(f"\n{i+1}. {concept['id']}: {concept['label']}")
        print(f"   Sinonim: {concept.get('synonyms', [])}")
        print(f"   Related: {concept.get('related', [])}")
        print(f"   Ayat: {concept.get('verses', [])}")
    
    return is_identical

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 