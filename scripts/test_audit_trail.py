#!/usr/bin/env python3
"""
Script untuk testing audit trail functionality
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db_connection
from app.api.services.ontology_service import OntologyService

def test_audit_trail():
    """Test audit trail functionality"""
    print("🧪 Testing Audit Trail Functionality")
    print("=" * 50)
    
    # Initialize ontology service with database storage
    ontology_service = OntologyService(storage_type='database')
    
    # Test user info
    test_user_info = {
        'user_id': 'test_user_123',
        'username': 'test_admin',
        'ip_address': '127.0.0.1',
        'user_agent': 'Test Script/1.0'
    }
    
    print("\n1. Testing CREATE operation...")
    try:
        # Create test concept
        test_concept = {
            'id': 'test_concept_audit',
            'label': 'Test Concept for Audit',
            'synonyms': ['test', 'audit test'],
            'broader': [],
            'narrower': [],
            'related': [],
            'verses': ['1:1', '2:2']
        }
        
        ontology_service.add_concept(test_concept, test_user_info)
        print("✅ CREATE operation logged successfully")
        
    except Exception as e:
        print(f"❌ Error in CREATE: {e}")
    
    print("\n2. Testing UPDATE operation...")
    try:
        # Update test concept
        updated_concept = {
            'id': 'test_concept_audit',
            'label': 'Updated Test Concept for Audit',
            'synonyms': ['test', 'audit test', 'updated'],
            'broader': ['parent_concept'],
            'narrower': [],
            'related': ['related_concept'],
            'verses': ['1:1', '2:2', '3:3']
        }
        
        ontology_service.update_concept('test_concept_audit', updated_concept, test_user_info)
        print("✅ UPDATE operation logged successfully")
        
    except Exception as e:
        print(f"❌ Error in UPDATE: {e}")
    
    print("\n3. Testing DELETE operation...")
    try:
        # Delete test concept
        ontology_service.delete_concept('test_concept_audit', test_user_info)
        print("✅ DELETE operation logged successfully")
        
    except Exception as e:
        print(f"❌ Error in DELETE: {e}")
    
    print("\n4. Testing Audit Log Retrieval...")
    try:
        # Get audit logs
        audit_logs = ontology_service.get_audit_log(limit=10)
        print(f"✅ Retrieved {len(audit_logs)} audit log entries")
        
        # Display recent logs
        for log in audit_logs[:3]:
            print(f"  - {log['timestamp']}: {log['action']} on {log['concept_id']} by {log['username']}")
            if log['changes']:
                print(f"    Changes: {log['changes']}")
        
    except Exception as e:
        print(f"❌ Error retrieving audit logs: {e}")
    
    print("\n5. Testing Audit Statistics...")
    try:
        # Get audit stats
        stats = ontology_service.get_audit_stats()
        print(f"✅ Audit Statistics:")
        print(f"  - Total entries: {stats.get('total_entries', 0)}")
        print(f"  - Recent activity (7 days): {stats.get('recent_activity', 0)}")
        print(f"  - Action counts: {stats.get('action_counts', {})}")
        print(f"  - Top users: {len(stats.get('top_users', []))}")
        
    except Exception as e:
        print(f"❌ Error retrieving audit stats: {e}")
    
    print("\n6. Testing Database Structure...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if audit table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='ontology_audit_log'
        """)
        
        if cursor.fetchone():
            print("✅ Audit table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(ontology_audit_log)")
            columns = cursor.fetchall()
            print(f"✅ Table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Check indexes
            cursor.execute("PRAGMA index_list(ontology_audit_log)")
            indexes = cursor.fetchall()
            print(f"✅ Table has {len(indexes)} indexes:")
            for idx in indexes:
                print(f"  - {idx[1]}")
            
        else:
            print("❌ Audit table does not exist")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database structure: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Audit Trail Testing Complete!")

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete test audit logs
        cursor.execute("DELETE FROM ontology_audit_log WHERE concept_id LIKE 'test_%'")
        deleted_count = cursor.rowcount
        
        # Delete test concepts
        cursor.execute("DELETE FROM ontology_concepts WHERE id LIKE 'test_%'")
        deleted_concepts = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleaned up {deleted_count} test audit logs and {deleted_concepts} test concepts")
        
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")

if __name__ == "__main__":
    print("Audit Trail Test Script")
    print("This script will test the audit trail functionality")
    
    response = input("\nDo you want to run the test? (y/n): ")
    if response.lower() == 'y':
        test_audit_trail()
        
        cleanup_response = input("\nDo you want to clean up test data? (y/n): ")
        if cleanup_response.lower() == 'y':
            cleanup_test_data()
    else:
        print("Test cancelled.") 