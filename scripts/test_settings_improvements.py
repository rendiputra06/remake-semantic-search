#!/usr/bin/env python3
"""
Script pengujian untuk perbaikan halaman settings dan evaluasi.
Menguji fitur pengaturan global, opsi tak terbatas, dan integrasi dengan evaluasi.
"""

import requests
import json
import time
import sys
import os

# Tambahkan path ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:5000"
TEST_USER = {
    "username": "test_user_settings",
    "password": "test123",
    "email": "test_settings@example.com"
}

class SettingsTester:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """Log hasil test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def register_user(self):
        """Register user untuk testing"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/register", data=TEST_USER)
            if response.status_code == 200:
                self.log_test("Register User", True, "User berhasil didaftarkan")
                return True
            else:
                self.log_test("Register User", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Register User", False, str(e))
            return False
    
    def login_user(self):
        """Login user"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", data=TEST_USER)
            if response.status_code == 200:
                self.log_test("Login User", True, "User berhasil login")
                return True
            else:
                self.log_test("Login User", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login User", False, str(e))
            return False
    
    def test_get_user_settings(self):
        """Test mengambil pengaturan user"""
        try:
            response = self.session.get(f"{BASE_URL}/api/models/user_settings")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    settings = data.get('data', {})
                    self.log_test("Get User Settings", True, f"Settings: {settings}")
                    return settings
                else:
                    self.log_test("Get User Settings", False, data.get('message', 'Unknown error'))
                    return None
            else:
                self.log_test("Get User Settings", False, f"Status code: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get User Settings", False, str(e))
            return None
    
    def test_update_settings(self, result_limit, threshold):
        """Test update pengaturan"""
        try:
            response = self.session.post(f"{BASE_URL}/settings", data={
                'result_limit': result_limit,
                'threshold': threshold
            })
            if response.status_code == 200:
                self.log_test(f"Update Settings ({result_limit}, {threshold})", True, "Pengaturan berhasil diupdate")
                return True
            else:
                self.log_test(f"Update Settings ({result_limit}, {threshold})", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"Update Settings ({result_limit}, {threshold})", False, str(e))
            return False
    
    def test_settings_validation(self):
        """Test validasi pengaturan"""
        # Test nilai negatif untuk result_limit
        try:
            response = self.session.post(f"{BASE_URL}/settings", data={
                'result_limit': -5,
                'threshold': 0.5
            })
            if response.status_code == 200:
                # Cek apakah ada pesan error
                if "tidak boleh negatif" in response.text:
                    self.log_test("Validation Negative Result Limit", True, "Validasi berhasil menolak nilai negatif")
                else:
                    self.log_test("Validation Negative Result Limit", False, "Validasi tidak menolak nilai negatif")
            else:
                self.log_test("Validation Negative Result Limit", True, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Validation Negative Result Limit", False, str(e))
        
        # Test threshold di luar range
        try:
            response = self.session.post(f"{BASE_URL}/settings", data={
                'result_limit': 10,
                'threshold': 1.5
            })
            if response.status_code == 200:
                # Cek apakah ada pesan error
                if "antara 0 dan 1" in response.text:
                    self.log_test("Validation Threshold Range", True, "Validasi berhasil menolak threshold di luar range")
                else:
                    self.log_test("Validation Threshold Range", False, "Validasi tidak menolak threshold di luar range")
            else:
                self.log_test("Validation Threshold Range", True, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Validation Threshold Range", False, str(e))
    
    def test_unlimited_option(self):
        """Test opsi tak terbatas"""
        # Set result_limit ke 0 (tak terbatas)
        if self.test_update_settings(0, 0.5):
            # Ambil settings lagi untuk memastikan
            settings = self.test_get_user_settings()
            if settings and settings.get('result_limit') == 1000:  # 0 dikonversi ke 1000
                self.log_test("Unlimited Option", True, "Nilai 0 berhasil dikonversi ke 1000")
            else:
                self.log_test("Unlimited Option", False, f"Expected 1000, got {settings.get('result_limit') if settings else 'None'}")
    
    def test_search_with_settings(self):
        """Test pencarian menggunakan pengaturan dari database"""
        # Set pengaturan tertentu
        if self.test_update_settings(5, 0.7):
            # Lakukan pencarian
            try:
                response = self.session.post(f"{BASE_URL}/api/search/search", json={
                    'query': 'shalat',
                    'model': 'word2vec'
                    # Tidak memberikan limit dan threshold, harus menggunakan dari settings
                })
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        results = data.get('data', {})
                        count = results.get('count', 0)
                        threshold = results.get('threshold', 0)
                        
                        # Cek apakah menggunakan pengaturan dari database
                        if count <= 5 and threshold == 0.7:
                            self.log_test("Search with Settings", True, f"Count: {count}, Threshold: {threshold}")
                        else:
                            self.log_test("Search with Settings", False, f"Expected count<=5, threshold=0.7, got count={count}, threshold={threshold}")
                    else:
                        self.log_test("Search with Settings", False, data.get('message', 'Unknown error'))
                else:
                    self.log_test("Search with Settings", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Search with Settings", False, str(e))
    
    def test_ontology_search_with_settings(self):
        """Test ontology search menggunakan pengaturan dari database"""
        # Set pengaturan tertentu
        if self.test_update_settings(3, 0.6):
            # Lakukan ontology search
            try:
                response = self.session.post(f"{BASE_URL}/api/ontology/search", json={
                    'query': 'ibadah',
                    'model': 'word2vec'
                    # Tidak memberikan limit dan threshold, harus menggunakan dari settings
                })
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        results = data.get('data', {})
                        count = len(results.get('results', []))
                        
                        # Cek apakah menggunakan pengaturan dari database
                        if count <= 3:
                            self.log_test("Ontology Search with Settings", True, f"Count: {count}")
                        else:
                            self.log_test("Ontology Search with Settings", False, f"Expected count<=3, got {count}")
                    else:
                        self.log_test("Ontology Search with Settings", False, data.get('message', 'Unknown error'))
                else:
                    self.log_test("Ontology Search with Settings", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Ontology Search with Settings", False, str(e))
    
    def test_evaluation_with_settings(self):
        """Test evaluasi menggunakan pengaturan dari database"""
        # Set pengaturan tertentu
        if self.test_update_settings(8, 0.8):
            # Ambil query evaluasi yang tersedia
            try:
                response = self.session.get(f"{BASE_URL}/api/evaluation/queries")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('data'):
                        query_id = data['data'][0]['id']
                        
                        # Jalankan evaluasi
                        eval_response = self.session.post(f"{BASE_URL}/api/evaluation/{query_id}/run", json={
                            'query_text': data['data'][0]['query_text'],
                            'selected_methods': ['word2vec']
                            # Tidak memberikan result_limit dan threshold, harus menggunakan dari settings
                        })
                        
                        if eval_response.status_code == 200:
                            eval_data = eval_response.json()
                            if eval_data.get('success'):
                                self.log_test("Evaluation with Settings", True, "Evaluasi berhasil menggunakan pengaturan dari database")
                            else:
                                self.log_test("Evaluation with Settings", False, eval_data.get('message', 'Unknown error'))
                        else:
                            self.log_test("Evaluation with Settings", False, f"Status code: {eval_response.status_code}")
                    else:
                        self.log_test("Evaluation with Settings", False, "Tidak ada query evaluasi tersedia")
                else:
                    self.log_test("Evaluation with Settings", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Evaluation with Settings", False, str(e))
    
    def test_settings_override(self):
        """Test override pengaturan dalam API"""
        # Set pengaturan default
        if self.test_update_settings(10, 0.5):
            # Lakukan pencarian dengan override
            try:
                response = self.session.post(f"{BASE_URL}/api/search/search", json={
                    'query': 'shalat',
                    'model': 'word2vec',
                    'limit': 3,  # Override limit
                    'threshold': 0.9  # Override threshold
                })
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        results = data.get('data', {})
                        count = results.get('count', 0)
                        threshold = results.get('threshold', 0)
                        
                        # Cek apakah override berhasil
                        if count <= 3 and threshold == 0.9:
                            self.log_test("Settings Override", True, f"Override berhasil: count={count}, threshold={threshold}")
                        else:
                            self.log_test("Settings Override", False, f"Override gagal: expected count<=3, threshold=0.9, got count={count}, threshold={threshold}")
                    else:
                        self.log_test("Settings Override", False, data.get('message', 'Unknown error'))
                else:
                    self.log_test("Settings Override", False, f"Status code: {response.status_code}")
            except Exception as e:
                self.log_test("Settings Override", False, str(e))
    
    def run_all_tests(self):
        """Jalankan semua test"""
        print("🚀 Memulai pengujian perbaikan halaman settings dan evaluasi...")
        print("=" * 60)
        
        # Setup
        if not self.register_user():
            print("❌ Gagal register user, skip test")
            return
        
        if not self.login_user():
            print("❌ Gagal login user, skip test")
            return
        
        # Test pengaturan dasar
        print("\n📋 Testing Pengaturan Dasar:")
        self.test_get_user_settings()
        self.test_update_settings(20, 0.6)
        self.test_get_user_settings()
        
        # Test validasi
        print("\n🔍 Testing Validasi:")
        self.test_settings_validation()
        
        # Test opsi tak terbatas
        print("\n♾️ Testing Opsi Tak Terbatas:")
        self.test_unlimited_option()
        
        # Test pencarian dengan pengaturan
        print("\n🔍 Testing Pencarian dengan Pengaturan:")
        self.test_search_with_settings()
        self.test_ontology_search_with_settings()
        
        # Test evaluasi dengan pengaturan
        print("\n📊 Testing Evaluasi dengan Pengaturan:")
        self.test_evaluation_with_settings()
        
        # Test override pengaturan
        print("\n⚙️ Testing Override Pengaturan:")
        self.test_settings_override()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 HASIL PENGUJIAN:")
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 SEMUA TEST BERHASIL!")
        else:
            print("⚠️ Beberapa test gagal. Periksa implementasi.")
        
        # Detail hasil
        print("\n📋 Detail Hasil:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = SettingsTester()
    tester.run_all_tests() 