import json
import os
from typing import Dict, List, Optional, Any
from backend.db import get_db_connection

ONTOLOGY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../ontology/ontology.json'))

class OntologyService:
    def __init__(self, storage_type='json', ontology_path=ONTOLOGY_PATH):
        """
        Initialize ontology service
        storage_type: 'json' or 'database'
        """
        self.storage_type = storage_type
        self.ontology_path = ontology_path
        self.concepts = []
        
        # Load data based on storage type
        if storage_type == 'database':
            self._load_from_database()
        else:
            self._load_from_json()
    
    def _load_from_json(self):
        """Load ontology from JSON file"""
        try:
            with open(self.ontology_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.concepts = data.get('concepts', [])
        except FileNotFoundError:
            print(f"⚠️  File JSON tidak ditemukan: {self.ontology_path}")
            self.concepts = []
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            self.concepts = []
    
    def _save_to_json(self):
        """Save ontology to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.ontology_path), exist_ok=True)
            with open(self.ontology_path, 'w', encoding='utf-8') as f:
                json.dump({'concepts': self.concepts}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    def _load_from_database(self):
        """Load ontology from database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if ontology table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ontology_concepts'
            """)
            
            if not cursor.fetchone():
                print("⚠️  Tabel ontology_concepts tidak ditemukan, menggunakan JSON")
                self.storage_type = 'json'
                self._load_from_json()
                return
            
            cursor.execute('SELECT * FROM ontology_concepts')
            rows = cursor.fetchall()
            
            self.concepts = []
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
                self.concepts.append(concept)
            
            conn.close()
            print(f"✅ Load dari database: {len(self.concepts)} konsep")
            
        except Exception as e:
            print(f"❌ Error loading from database: {e}")
            print("🔄 Fallback ke JSON...")
            self.storage_type = 'json'
            self._load_from_json()
    
    def _save_to_database(self):
        """Save ontology to database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create table if not exists
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
            
            # Clear existing data
            cursor.execute('DELETE FROM ontology_concepts')
            
            # Insert new data
            for concept in self.concepts:
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
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return False
    
    def _save_ontology(self):
        """Save ontology based on storage type"""
        if self.storage_type == 'database':
            return self._save_to_database()
        else:
            return self._save_to_json()
    
    def sync_to_database(self):
        """Sync JSON ontology to database"""
        if self.storage_type == 'json':
            return self._save_to_database()
        return True
    
    def export_to_json(self):
        """Export database ontology to JSON"""
        if self.storage_type == 'database':
            return self._save_to_json()
        return True
    
    def switch_storage(self, new_storage_type):
        """Switch storage type"""
        if new_storage_type == self.storage_type:
            return True
        
        if new_storage_type == 'database':
            # Save current data to database
            success = self._save_to_database()
            if success:
                self.storage_type = 'database'
                print("✅ Berhasil switch ke database storage")
            return success
        else:
            # Save current data to JSON
            success = self._save_to_json()
            if success:
                self.storage_type = 'json'
                print("✅ Berhasil switch ke JSON storage")
            return success

    def find_concept(self, keyword):
        """Cari konsep berdasarkan id, label, atau sinonim (case-insensitive)"""
        keyword = keyword.lower()
        for c in self.concepts:
            if c['id'] == keyword or c['label'].lower() == keyword or keyword in [s.lower() for s in c.get('synonyms', [])]:
                return c
        return None

    def get_related(self, concept_id):
        """Ambil konsep terkait (related, broader, narrower, sinonim)"""
        c = self.find_concept(concept_id)
        if not c:
            return None
        related_ids = set(c.get('related', []) + c.get('broader', []) + c.get('narrower', []) + [c['id']] + [s for s in c.get('synonyms', [])])
        related = []
        for cid in related_ids:
            found = self.find_concept(cid)
            if found:
                related.append(found)
        return related

    def get_verses(self, concept_id):
        c = self.find_concept(concept_id)
        if not c:
            return []
        return c.get('verses', [])

    def get_all(self):
        return self.concepts

    def add_concept(self, concept):
        # id harus unik
        if self.find_concept(concept['id']):
            raise ValueError('ID konsep sudah ada')
        self.concepts.append(concept)
        self._save_ontology()

    def update_concept(self, concept_id, new_data):
        for i, c in enumerate(self.concepts):
            if c['id'] == concept_id:
                self.concepts[i] = new_data
                self._save_ontology()
                return
        raise ValueError('Konsep tidak ditemukan')

    def delete_concept(self, concept_id):
        before = len(self.concepts)
        self.concepts = [c for c in self.concepts if c['id'] != concept_id]
        if len(self.concepts) == before:
            raise ValueError('Konsep tidak ditemukan')
        self._save_ontology()
    
    def get_storage_info(self):
        """Get storage information"""
        return {
            'storage_type': self.storage_type,
            'concept_count': len(self.concepts),
            'json_path': self.ontology_path if self.storage_type == 'json' else None
        } 