#!/usr/bin/env python3
"""
Script untuk menguji perbaikan caching pada ensemble system
- Verifikasi model tidak di-load berulang kali
- Test performance improvement
- Monitor memory usage
"""

import sys
import os
import time
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ensemble_caching():
    """Test ensemble API dengan caching untuk memverifikasi tidak ada reload berulang"""
    
    base_url = "http://localhost:5000"
    
    # Test cases untuk memverifikasi caching
    test_cases = [
        {
            "name": "Test 1 - Query 'ibadah'",
            "data": {
                "query": "ibadah",
                "method": "weighted",
                "threshold": 0.5,
                "limit": 10,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test 2 - Query 'shalat' (should use cached models)",
            "data": {
                "query": "shalat",
                "method": "weighted",
                "threshold": 0.5,
                "limit": 10,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test 3 - Query 'puasa' dengan meta-ensemble",
            "data": {
                "query": "puasa",
                "method": "meta",
                "threshold": 0.5,
                "limit": 15,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test 4 - Query 'zakat' dengan voting",
            "data": {
                "query": "zakat",
                "method": "voting",
                "threshold": 0.5,
                "limit": 20,
                "w2v_weight": 1.0,
                "ft_weight": 1.0,
                "glove_weight": 1.0
            }
        },
        {
            "name": "Test 5 - Query 'haji' dengan custom weights",
            "data": {
                "query": "haji",
                "method": "weighted",
                "threshold": 0.5,
                "limit": 10,
                "w2v_weight": 1.5,
                "ft_weight": 0.8,
                "glove_weight": 1.2
            }
        }
    ]
    
    print("🧪 Testing Ensemble Caching Improvements")
    print("=" * 60)
    print("Expected behavior: First request loads models, subsequent requests use cached models")
    print("=" * 60)
    
    response_times = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/api/models/ensemble/test",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    results = data.get('results', [])
                    print(f"✅ Success: {len(results)} results found")
                    print(f"⏱️  Response time: {response_time:.2f} seconds")
                    
                    # Show first few results
                    for j, res in enumerate(results[:2]):
                        print(f"   {j+1}. {res.get('surah_name', 'N/A')} {res.get('ayat_number', 'N/A')} - Score: {res.get('similarity', 0):.3f}")
                    
                    if len(results) > 2:
                        print(f"   ... and {len(results) - 2} more results")
                        
                else:
                    print(f"❌ API Error: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
    
    # Analyze response times
    print(f"\n📊 Performance Analysis")
    print("=" * 40)
    if len(response_times) >= 2:
        first_time = response_times[0]
        avg_subsequent = sum(response_times[1:]) / len(response_times[1:])
        improvement = ((first_time - avg_subsequent) / first_time) * 100
        
        print(f"First request time: {first_time:.2f}s")
        print(f"Average subsequent requests: {avg_subsequent:.2f}s")
        print(f"Performance improvement: {improvement:.1f}%")
        
        if improvement > 20:
            print("✅ Caching is working effectively!")
        elif improvement > 10:
            print("⚠️  Caching shows some improvement")
        else:
            print("❌ Caching may not be working as expected")
    else:
        print("⚠️  Not enough data for performance analysis")

def test_memory_usage():
    """Test memory usage untuk memverifikasi tidak ada memory leak"""
    
    print(f"\n💾 Memory Usage Test")
    print("=" * 40)
    
    try:
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Test multiple requests
        base_url = "http://localhost:5000"
        
        print("Testing memory usage with multiple requests...")
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Make several requests
        for i in range(5):
            response = requests.post(
                f"{base_url}/api/models/ensemble/test",
                json={
                    "query": f"test_query_{i}",
                    "method": "weighted",
                    "threshold": 0.5,
                    "limit": 10,
                    "w2v_weight": 1.0,
                    "ft_weight": 1.0,
                    "glove_weight": 1.0
                },
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"Request {i+1} memory: {current_memory:.2f} MB")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        if memory_increase < 50:  # Less than 50MB increase
            print("✅ Memory usage is stable")
        else:
            print("⚠️  Memory usage increased significantly")
            
    except ImportError:
        print("⚠️  psutil not available, skipping memory test")
    except Exception as e:
        print(f"❌ Memory test failed: {e}")

def test_caching_consistency():
    """Test konsistensi hasil dengan caching"""
    
    print(f"\n🔄 Caching Consistency Test")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    # Test data
    test_data = {
        "query": "ibadah",
        "method": "weighted",
        "threshold": 0.5,
        "limit": 10,
        "w2v_weight": 1.0,
        "ft_weight": 1.0,
        "glove_weight": 1.0
    }
    
    results = []
    
    # Make multiple identical requests
    for i in range(3):
        try:
            response = requests.post(
                f"{base_url}/api/models/ensemble/test",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    results.append(data.get('results', []))
                    print(f"Request {i+1}: {len(results[-1])} results")
                else:
                    print(f"Request {i+1}: API Error")
            else:
                print(f"Request {i+1}: HTTP Error {response.status_code}")
                
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")
    
    # Compare results
    if len(results) >= 2:
        first_result = results[0]
        consistent = True
        
        for i, result in enumerate(results[1:], 1):
            if len(result) != len(first_result):
                print(f"⚠️  Result count mismatch: {len(first_result)} vs {len(result)}")
                consistent = False
                break
            
            # Compare first few results
            for j in range(min(3, len(first_result))):
                if (first_result[j].get('verse_id') != result[j].get('verse_id') or
                    abs(first_result[j].get('similarity', 0) - result[j].get('similarity', 0)) > 0.001):
                    print(f"⚠️  Result mismatch at position {j}")
                    consistent = False
                    break
        
        if consistent:
            print("✅ Results are consistent across requests")
        else:
            print("❌ Results are inconsistent")
    else:
        print("⚠️  Not enough data for consistency test")

if __name__ == "__main__":
    print("🚀 Starting Ensemble Caching Test Suite")
    print("=" * 60)
    
    # Test caching performance
    test_ensemble_caching()
    
    # Test memory usage
    test_memory_usage()
    
    # Test caching consistency
    test_caching_consistency()
    
    print("\n🎉 Caching test suite completed!")
    print("=" * 60) 