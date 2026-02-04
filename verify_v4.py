
import os
import sys
import unittest
import json
import io
from run import app
from backend.db import init_db, get_custom_evaluation

class TestEvaluationV4(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()  # Ensure DB and tables exist

    def login(self, username, password):
        return self.client.post('/auth/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_01_admin_login(self):
        rv = self.login('admin', 'admin123')
        self.assertIn(b'Admin Panel', rv.data)
        print("Login successful.")

    def test_02_upload_csv(self):
        self.login('admin', 'admin123')
        
        # Create dummy CSV
        csv_content = (
            "Topic,W2V_Threshold,FT_Threshold,GV_Threshold,Precision,Recall,F1_Score,TP,FP,FN\n"
            "TestQuery123,0.5,0.6,0.7,0.9,0.8,0.85,90,10,20\n"
        ).encode('utf-8')
        
        data = {
            'file': (io.BytesIO(csv_content), 'test_upload.csv')
        }
        
        rv = self.client.post('/admin/custom_eval/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'Berhasil memproses', rv.data)
        
        # Verify in DB
        result = get_custom_evaluation("TestQuery123")
        self.assertIsNotNone(result)
        self.assertEqual(result['f1_score'], 0.85)
        print("CSV Upload and DB Verification successful.")

    def test_03_api_custom_override(self):
        # Must execute within app context or simulated request
        # Mocking query_text sending to API
        payload = {
            'query_text': 'TestQuery123',
            'selected_methods': ['lexical'],
            'result_limit': 10
        }
        
        rv = self.client.post('/api/evaluation_v4/0/run', 
                            data=json.dumps(payload),
                            content_type='application/json')
        
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['label'], 'Custom CSV Result')
        self.assertEqual(data['results'][0]['f1'], 0.85)
        print("API Custom Override successful.")

    def test_04_api_fallback(self):
        payload = {
            'query_text': 'UnknownQueryForFallback',
            'selected_methods': ['lexical'], # Only test lexical for speed
            'result_limit': 10
        }
        
        # It's expected to fail "Ayat relevan belum diinput" if no Relevant Verses, 
        # but that proves it went past the Override check.
        rv = self.client.post('/api/evaluation_v4/999/run', 
                            data=json.dumps(payload),
                            content_type='application/json')
        
        data = json.loads(rv.data)
        # If it returns "Ayat relevan belum diinput", it means it tried to run standard logic
        # If it returns Custom Result, it failed.
        
        if not data['success']:
             self.assertIn('Ayat relevan belum diinput', data.get('message', ''))
        else:
             # If it somehow succeeded (if verses existed for ID 999), ensure it's NOT custom
             self.assertNotEqual(data['results'][0]['label'], 'Custom CSV Result')
             
        print("API Fallback logic successful (attempted standard run).")

if __name__ == '__main__':
    unittest.main()
