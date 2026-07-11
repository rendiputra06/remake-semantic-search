import unittest
import json
from run import app
from backend.db import init_db

class TestVectorExplorerAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_01_get_vectors_default(self):
        # Default Word2Vec model, page 1, limit 20
        rv = self.client.get('/api/vector-explorer/query?model_type=word2vec&page=1&limit=20')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 20)
        self.assertEqual(data['current_page'], 1)
        self.assertEqual(data['limit'], 20)
        self.assertGreater(data['total_verses'], 6000)
        
        # Verify first item schema
        first_item = data['data'][0]
        self.assertIn('verse_id', first_item)
        self.assertIn('arabic', first_item)
        self.assertIn('translation', first_item)
        self.assertIn('vector', first_item)
        self.assertEqual(len(first_item['vector']), 200) # 200 dimensions
        print("[OK] test_01_get_vectors_default passed.")

    def test_02_get_vectors_search(self):
        # Search filter "2:255" (Ayat Kursi)
        rv = self.client.get('/api/vector-explorer/query?model_type=word2vec&search=2:255')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['total_verses'], 1)
        self.assertEqual(data['data'][0]['verse_id'], '2:255')
        print("[OK] test_02_get_vectors_search passed.")

    def test_03_get_vectors_matching(self):
        # Match word "iman"
        rv = self.client.get('/api/vector-explorer/query?model_type=word2vec&match_word=iman')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['word_vector'])
        self.assertEqual(len(data['word_vector']), 200)
        
        # Verify similarity scores are returned
        first_item = data['data'][0]
        self.assertIn('similarity', first_item)
        self.assertGreaterEqual(first_item['similarity'], -1.0)
        self.assertLessEqual(first_item['similarity'], 1.0)
        
        # Verify sorting (first item similarity must be greater than or equal to second)
        if len(data['data']) > 1:
            self.assertGreaterEqual(data['data'][0]['similarity'], data['data'][1]['similarity'])
            
        print("[OK] test_03_get_vectors_matching passed.")

    def test_04_get_vectors_oov(self):
        # Out-Of-Vocabulary word should return 400
        rv = self.client.get('/api/vector-explorer/query?model_type=word2vec&match_word=xyzabc123nonexistent')
        self.assertEqual(rv.status_code, 400)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        self.assertIn('tidak dikenali oleh model', data['message'])
        print("[OK] test_04_get_vectors_oov passed.")

    def test_05_get_details_valid(self):
        # Query details of Al-Baqarah 2:255
        rv = self.client.get('/api/vector-explorer/details?model_type=word2vec&verse_id=2:255&match_word=iman')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['verse_id'], '2:255')
        self.assertEqual(data['surah_name'], 'Al-Baqarah')
        self.assertIn('preprocessing', data)
        self.assertIn('lowercase', data['preprocessing'])
        self.assertIn('token_details', data)
        self.assertEqual(len(data['final_vector']), 200)
        self.assertEqual(len(data['mean_vector']), 200)
        self.assertEqual(len(data['l2_vector']), 200)
        self.assertIsNotNone(data['word_vector'])
        print("[OK] test_05_get_details_valid passed.")

    def test_06_get_details_invalid(self):
        # Query invalid verse
        rv = self.client.get('/api/vector-explorer/details?model_type=word2vec&verse_id=999:999')
        self.assertEqual(rv.status_code, 404)
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        self.assertIn('tidak ditemukan', data['message'])
        print("[OK] test_06_get_details_invalid passed.")

if __name__ == '__main__':
    unittest.main()
