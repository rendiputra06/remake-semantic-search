#!/usr/bin/env python3
"""
Script untuk menguji perbaikan halaman evaluasi
"""

import requests
import json
import time
import random

BASE_URL = "http://localhost:5000"

def test_api_connection():
    """Test koneksi ke API"""
    try:
        response = requests.get(f"{BASE_URL}/api/query")
        if response.status_code == 200:
            print("✅ API connection successful")
            return True
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def create_test_query(text="Test query evaluasi"):
    """Buat query test"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"text": text},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                query_id = data.get("query_id")
                print(f"✅ Test query created with ID: {query_id}")
                return query_id
        print(f"❌ Failed to create test query: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error creating test query: {e}")
        return None

def add_test_verses(query_id, count=50):
    """Tambah ayat test untuk load more testing"""
    test_verses = [
        "1:1", "1:2", "1:3", "1:4", "1:5", "1:6", "1:7",
        "2:1", "2:2", "2:3", "2:4", "2:5", "2:6", "2:7", "2:8", "2:9", "2:10",
        "3:1", "3:2", "3:3", "3:4", "3:5", "3:6", "3:7", "3:8", "3:9", "3:10",
        "4:1", "4:2", "4:3", "4:4", "4:5", "4:6", "4:7", "4:8", "4:9", "4:10",
        "5:1", "5:2", "5:3", "5:4", "5:5", "5:6", "5:7", "5:8", "5:9", "5:10",
        "6:1", "6:2", "6:3", "6:4", "6:5", "6:6", "6:7", "6:8", "6:9", "6:10",
        "7:1", "7:2", "7:3", "7:4", "7:5", "7:6", "7:7", "7:8", "7:9", "7:10",
        "8:1", "8:2", "8:3", "8:4", "8:5", "8:6", "8:7", "8:8", "8:9", "8:10",
        "9:1", "9:2", "9:3", "9:4", "9:5", "9:6", "9:7", "9:8", "9:9", "9:10",
        "10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10"
    ]
    
    added_count = 0
    for i, verse in enumerate(test_verses[:count]):
        try:
            response = requests.post(
                f"{BASE_URL}/api/query/{query_id}/relevant_verses",
                json={"verse_ref": verse},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    added_count += 1
                else:
                    print(f"⚠️ Failed to add verse {verse}: {data.get('message')}")
            else:
                print(f"⚠️ HTTP error adding verse {verse}: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error adding verse {verse}: {e}")
    
    print(f"✅ Added {added_count} test verses")
    return added_count

def test_load_relevant_verses(query_id):
    """Test load relevant verses"""
    try:
        response = requests.get(f"{BASE_URL}/api/query/{query_id}/relevant_verses")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                verses = data.get("data", [])
                print(f"✅ Loaded {len(verses)} relevant verses")
                return verses
        print(f"❌ Failed to load relevant verses: {response.text}")
        return []
    except Exception as e:
        print(f"❌ Error loading relevant verses: {e}")
        return []

def test_evaluation_results(query_id):
    """Test load evaluation results"""
    try:
        response = requests.get(f"{BASE_URL}/api/query/{query_id}/evaluation_results")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", [])
                print(f"✅ Loaded {len(results)} evaluation results")
                return results
        print(f"❌ Failed to load evaluation results: {response.text}")
        return []
    except Exception as e:
        print(f"❌ Error loading evaluation results: {e}")
        return []

def test_run_evaluation(query_id):
    """Test run evaluation"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/evaluation/{query_id}/run",
            json={
                "query_text": "Test query evaluasi",
                "result_limit": 10,
                "threshold": 0.5,
                "selected_methods": ["lexical", "word2vec"]
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("results", [])
                print(f"✅ Evaluation completed with {len(results)} results")
                return results
        print(f"❌ Failed to run evaluation: {response.text}")
        return []
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        return []

def test_delete_relevant_verse(query_id, verse_id):
    """Test delete relevant verse"""
    try:
        response = requests.delete(f"{BASE_URL}/api/query/relevant_verse/{verse_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Deleted relevant verse {verse_id}")
                return True
        print(f"❌ Failed to delete relevant verse: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error deleting relevant verse: {e}")
        return False

def test_delete_query(query_id):
    """Test delete query"""
    try:
        response = requests.delete(f"{BASE_URL}/api/query/{query_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Deleted query {query_id}")
                return True
        print(f"❌ Failed to delete query: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error deleting query: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Evaluasi Page Improvements")
    print("=" * 50)
    
    # Test 1: API Connection
    print("\n1. Testing API Connection...")
    if not test_api_connection():
        print("❌ Cannot proceed without API connection")
        return
    
    # Test 2: Create Test Query
    print("\n2. Creating Test Query...")
    query_id = create_test_query("Test query untuk load more dan pagination")
    if not query_id:
        print("❌ Cannot proceed without test query")
        return
    
    # Test 3: Add Test Verses (for load more testing)
    print("\n3. Adding Test Verses...")
    verse_count = add_test_verses(query_id, 50)
    if verse_count == 0:
        print("⚠️ No verses added, but continuing...")
    
    # Test 4: Load Relevant Verses
    print("\n4. Testing Load Relevant Verses...")
    verses = test_load_relevant_verses(query_id)
    
    # Test 5: Test Evaluation Results (should be empty initially)
    print("\n5. Testing Initial Evaluation Results...")
    initial_results = test_evaluation_results(query_id)
    if len(initial_results) == 0:
        print("✅ Correctly shows no evaluation results initially")
    
    # Test 6: Run Evaluation
    print("\n6. Running Evaluation...")
    eval_results = test_run_evaluation(query_id)
    
    # Test 7: Test Evaluation Results (should have data now)
    print("\n7. Testing Evaluation Results After Run...")
    final_results = test_evaluation_results(query_id)
    if len(final_results) > 0:
        print("✅ Evaluation results now available")
        for result in final_results:
            print(f"   - {result.get('model')}: P={result.get('precision')}, R={result.get('recall')}, F1={result.get('f1')}")
    else:
        print("❌ No evaluation results found after run")
    
    # Test 8: Test Delete Relevant Verse (if any verses exist)
    if verses:
        print("\n8. Testing Delete Relevant Verse...")
        first_verse = verses[0]
        verse_id = first_verse.get('id')
        if verse_id:
            test_delete_relevant_verse(query_id, verse_id)
    
    # Test 9: Test Delete Query
    print("\n9. Testing Delete Query...")
    test_delete_query(query_id)
    
    print("\n" + "=" * 50)
    print("🎉 Evaluasi Page Improvements Test Completed!")
    print("\nManual Testing Required:")
    print("1. Open http://localhost:5000/evaluasi")
    print("2. Create a query and add 50+ verses")
    print("3. Test 'Detail Ayat Relevan' modal with load more")
    print("4. Run evaluation and test pagination in results")
    print("5. Verify 'Hasil Evaluasi Terakhir' shows data")

if __name__ == "__main__":
    main() 