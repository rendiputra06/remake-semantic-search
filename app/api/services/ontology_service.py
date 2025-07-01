import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
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
    
    def _create_audit_table(self, cursor):
        """Create audit log table if not exists"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ontology_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id TEXT NOT NULL,
                action TEXT NOT NULL,
                user_id TEXT,
                username TEXT,
                old_data TEXT,
                new_data TEXT,
                changes TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_concept_id ON ontology_audit_log(concept_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON ontology_audit_log(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON ontology_audit_log(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON ontology_audit_log(user_id)')
    
    def _log_audit(self, concept_id: str, action: str, old_data: dict = None, 
                   new_data: dict = None, user_info: dict = None):
        """Log audit trail for concept changes"""
        if self.storage_type != 'database':
            return  # Only log for database storage
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create audit table if not exists
            self._create_audit_table(cursor)
            
            # Prepare changes summary
            changes = []
            if old_data and new_data:
                for field in ['label', 'synonyms', 'broader', 'narrower', 'related', 'verses']:
                    old_val = old_data.get(field, [])
                    new_val = new_data.get(field, [])
                    if old_val != new_val:
                        changes.append(f"{field}: {old_val} → {new_val}")
            
            # Insert audit log
            cursor.execute('''
                INSERT INTO ontology_audit_log 
                (concept_id, action, user_id, username, old_data, new_data, changes, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                concept_id,
                action,
                user_info.get('user_id') if user_info else None,
                user_info.get('username') if user_info else None,
                json.dumps(old_data, ensure_ascii=False) if old_data else None,
                json.dumps(new_data, ensure_ascii=False) if new_data else None,
                '; '.join(changes) if changes else None,
                user_info.get('ip_address') if user_info else None,
                user_info.get('user_agent') if user_info else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error logging audit: {e}")
    
    def get_audit_log(self, concept_id: str = None, action: str = None, 
                     limit: int = 100, offset: int = 0) -> List[dict]:
        """Get audit log entries"""
        if self.storage_type != 'database':
            return []
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create audit table if not exists
            self._create_audit_table(cursor)
            
            # Build query
            query = "SELECT * FROM ontology_audit_log WHERE 1=1"
            params = []
            
            if concept_id:
                query += " AND concept_id = ?"
                params.append(concept_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            audit_logs = []
            for row in rows:
                audit_log = {
                    'id': row['id'],
                    'concept_id': row['concept_id'],
                    'action': row['action'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'old_data': json.loads(row['old_data']) if row['old_data'] else None,
                    'new_data': json.loads(row['new_data']) if row['new_data'] else None,
                    'changes': row['changes'],
                    'ip_address': row['ip_address'],
                    'user_agent': row['user_agent'],
                    'timestamp': row['timestamp']
                }
                audit_logs.append(audit_log)
            
            conn.close()
            return audit_logs
            
        except Exception as e:
            print(f"❌ Error getting audit log: {e}")
            return []
    
    def get_audit_stats(self) -> dict:
        """Get audit statistics"""
        if self.storage_type != 'database':
            return {}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create audit table if not exists
            self._create_audit_table(cursor)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM ontology_audit_log")
            total = cursor.fetchone()['total']
            
            # Get action counts
            cursor.execute("""
                SELECT action, COUNT(*) as count 
                FROM ontology_audit_log 
                GROUP BY action
            """)
            action_counts = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # Get recent activity (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as recent 
                FROM ontology_audit_log 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            recent = cursor.fetchone()['recent']
            
            # Get top users
            cursor.execute("""
                SELECT username, COUNT(*) as count 
                FROM ontology_audit_log 
                WHERE username IS NOT NULL
                GROUP BY username 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_users = [{'username': row['username'], 'count': row['count']} 
                        for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_entries': total,
                'action_counts': action_counts,
                'recent_activity': recent,
                'top_users': top_users
            }
            
        except Exception as e:
            print(f"❌ Error getting audit stats: {e}")
            return {}
    
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

    def add_concept(self, concept, user_info=None):
        # id harus unik
        if self.find_concept(concept['id']):
            raise ValueError('ID konsep sudah ada')
        
        # Log audit trail
        self._log_audit(concept['id'], 'CREATE', new_data=concept, user_info=user_info)
        
        self.concepts.append(concept)
        self._save_ontology()

    def update_concept(self, concept_id, new_data, user_info=None):
        # Find old data for audit
        old_data = None
        for c in self.concepts:
            if c['id'] == concept_id:
                old_data = c.copy()
                break
        
        if not old_data:
            raise ValueError('Konsep tidak ditemukan')
        
        # Log audit trail
        self._log_audit(concept_id, 'UPDATE', old_data=old_data, new_data=new_data, user_info=user_info)
        
        # Update concept
        for i, c in enumerate(self.concepts):
            if c['id'] == concept_id:
                self.concepts[i] = new_data
                self._save_ontology()
                return
        raise ValueError('Konsep tidak ditemukan')

    def delete_concept(self, concept_id, user_info=None):
        # Find old data for audit
        old_data = None
        for c in self.concepts:
            if c['id'] == concept_id:
                old_data = c.copy()
                break
        
        if not old_data:
            raise ValueError('Konsep tidak ditemukan')
        
        # Log audit trail
        self._log_audit(concept_id, 'DELETE', old_data=old_data, user_info=user_info)
        
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