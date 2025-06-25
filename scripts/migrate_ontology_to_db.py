#!/usr/bin/env python3
"""
Script untuk migrasi ontologi dari JSON ke database
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db_connection

def create_ontology_table(cursor):
    """Buat tabel ontology_concepts jika belum ada"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ontology_concepts (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            synonyms TEXT,
            broader TEXT,
            narrower TEXT,
            related TEXT,
            verses TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def backup_json_ontology(json_path, backup_dir):
    """Backup file JSON sebelum migrasi"""
    if not os.path.exists(json_path):
        print(f"❌ File JSON tidak ditemukan: {json_path}")
        return False
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"ontology_backup_{timestamp}.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"✅ Backup berhasil: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error backup: {e}")
        return False

def load_json_ontology(json_path):
    """Load data ontologi dari JSON"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Load JSON berhasil: {len(data.get('concepts', []))} konsep")
        return data
    except Exception as e:
        print(f"❌ Error load JSON: {e}")
        return None

def validate_concept(concept):
    """Validasi struktur konsep"""
    required_fields = ['id', 'label']
    optional_fields = ['synonyms', 'broader', 'narrower', 'related', 'verses']
    
    # Check required fields
    for field in required_fields:
        if field not in concept:
            print(f"⚠️  Konsep {concept.get('id', 'unknown')} missing field: {field}")
            return False
    
    # Ensure optional fields are lists
    for field in optional_fields:
        if field in concept and not isinstance(concept[field], list):
            print(f"⚠️  Konsep {concept['id']} field {field} bukan list")
            concept[field] = []
    
    return True

def migrate_to_database(json_data):
    """Migrasi data ke database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create table
        create_ontology_table(cursor)
        
        # Clear existing data
        cursor.execute('DELETE FROM ontology_concepts')
        print("🗑️  Data lama dihapus")
        
        # Insert concepts
        concepts = json_data.get('concepts', [])
        valid_concepts = 0
        invalid_concepts = 0
        
        for concept in concepts:
            if validate_concept(concept):
                cursor.execute('''
                    INSERT INTO ontology_concepts 
                    (id, label, synonyms, broader, narrower, related, verses)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    concept['id'],
                    concept['label'],
                    json.dumps(concept.get('synonyms', [])),
                    json.dumps(concept.get('broader', [])),
                    json.dumps(concept.get('narrower', [])),
                    json.dumps(concept.get('related', [])),
                    json.dumps(concept.get('verses', []))
                ))
                valid_concepts += 1
            else:
                invalid_concepts += 1
        
        conn.commit()
        print(f"✅ Migrasi berhasil: {valid_concepts} konsep valid, {invalid_concepts} konsep invalid")
        
        # Verify migration
        cursor.execute('SELECT COUNT(*) as count FROM ontology_concepts')
        count = cursor.fetchone()['count']
        print(f"📊 Total konsep di database: {count}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error migrasi: {e}")
        return False
    finally:
        conn.close()

def verify_migration():
    """Verifikasi hasil migrasi"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ontology_concepts'
        """)
        if not cursor.fetchone():
            print("❌ Tabel ontology_concepts tidak ditemukan")
            return False
        
        # Check data
        cursor.execute('SELECT COUNT(*) as count FROM ontology_concepts')
        count = cursor.fetchone()['count']
        
        if count == 0:
            print("❌ Tidak ada data di tabel ontology_concepts")
            return False
        
        # Sample data
        cursor.execute('SELECT id, label FROM ontology_concepts LIMIT 5')
        samples = cursor.fetchall()
        
        print(f"✅ Verifikasi berhasil: {count} konsep")
        print("📋 Sample data:")
        for sample in samples:
            print(f"  - {sample['id']}: {sample['label']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifikasi: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main function"""
    print("🚀 Memulai migrasi ontologi dari JSON ke database...")
    
    # Paths
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ontology', 'ontology.json')
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ontology', 'backups')
    
    print(f"📁 JSON path: {json_path}")
    print(f"📁 Backup dir: {backup_dir}")
    
    # Step 1: Backup JSON
    print("\n📦 Step 1: Backup JSON...")
    if not backup_json_ontology(json_path, backup_dir):
        print("❌ Backup gagal, migrasi dibatalkan")
        return False
    
    # Step 2: Load JSON data
    print("\n📖 Step 2: Load JSON data...")
    json_data = load_json_ontology(json_path)
    if not json_data:
        print("❌ Load JSON gagal, migrasi dibatalkan")
        return False
    
    # Step 3: Migrate to database
    print("\n🔄 Step 3: Migrate to database...")
    if not migrate_to_database(json_data):
        print("❌ Migrasi gagal")
        return False
    
    # Step 4: Verify migration
    print("\n✅ Step 4: Verify migration...")
    if not verify_migration():
        print("❌ Verifikasi gagal")
        return False
    
    print("\n🎉 Migrasi berhasil selesai!")
    print("\n📝 Langkah selanjutnya:")
    print("1. Update ontology service untuk menggunakan database")
    print("2. Test fitur ontologi")
    print("3. Backup database secara berkala")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 