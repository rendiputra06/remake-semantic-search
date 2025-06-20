import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel

class EnsembleEmbeddingModel:
    """
    Model ensemble untuk menggabungkan Word2Vec, FastText, dan GloVe dengan metode averaging.
    """
    def __init__(self, 
                 word2vec_model: Word2VecModel, 
                 fasttext_model: FastTextModel, 
                 glove_model: GloVeModel):
        self.word2vec_model = word2vec_model
        self.fasttext_model = fasttext_model
        self.glove_model = glove_model
        self.verse_data = None  # Akan diambil dari salah satu model (diasumsikan sama)
        self.verse_vectors = {}  # vektor ensemble untuk setiap ayat

    def load_models(self):
        """
        Memastikan semua model sudah dimuat.
        """
        print("ensemble: Loading models...")
        self.word2vec_model.load_model()
        self.fasttext_model.load_model()
        self.glove_model.load_model()

    def load_verse_vectors(self):
        """
        Memuat vektor ayat dari masing-masing model dan membangun vektor ensemble (averaging).
        """
        print("ensemble: Loading verse vectors...")
        self.word2vec_model.load_verse_vectors()
        self.fasttext_model.load_verse_vectors()
        self.glove_model.load_verse_vectors()
        # Ambil verse_data dari salah satu model (diasumsikan sama)
        self.verse_data = self.word2vec_model.verse_data
        # Averaging vektor antar model
        verse_ids = set(self.word2vec_model.verse_vectors.keys()) & set(self.fasttext_model.verse_vectors.keys()) & set(self.glove_model.verse_vectors.keys())
        for verse_id in verse_ids:
            v1 = self.word2vec_model.verse_vectors.get(verse_id)
            v2 = self.fasttext_model.verse_vectors.get(verse_id)
            v3 = self.glove_model.verse_vectors.get(verse_id)
            vectors = [v for v in [v1, v2, v3] if v is not None]
            if len(vectors) < 2:
                # Lewati jika kurang dari 2 model yang punya vektor valid
                continue
            shapes = [v.shape for v in vectors]
            if not all(s == shapes[0] for s in shapes):
                # print(f"[Ensemble] Shape mismatch for verse_id {verse_id}: {[v.shape for v in vectors]}")
                continue
            avg_vec = np.mean(vectors, axis=0)
            self.verse_vectors[verse_id] = avg_vec

    def _calculate_query_vector(self, tokens: List[str]) -> np.ndarray:
        """
        Menghitung vektor query dengan averaging dari ketiga model.
        """
        v1 = self.word2vec_model._calculate_verse_vector(tokens)
        v2 = self.fasttext_model._calculate_verse_vector(tokens)
        v3 = self.glove_model._calculate_verse_vector(tokens)
        # Jika salah satu None, abaikan dari averaging
        vectors = [v for v in [v1, v2, v3] if v is not None]
        if not vectors:
            return None
        return np.mean(vectors, axis=0)


    def search(self, query: str, language: str = 'id', limit: int = 10, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian ensemble.
        Mengumpulkan hasil dari setiap model, menggabungkannya, dan menghitung skor rata-rata serta menyimpan skor individual.
        """
        # 1. Dapatkan hasil dari setiap model
        results_w2v = {res['verse_id']: res for res in self.word2vec_model.search(query, language, limit=limit*3, threshold=threshold)}
        results_ft = {res['verse_id']: res for res in self.fasttext_model.search(query, language, limit=limit*3, threshold=threshold)}
        results_glove = {res['verse_id']: res for res in self.glove_model.search(query, language, limit=limit*3, threshold=threshold)}

        # 2. Gabungkan semua verse_id yang unik
        all_verse_ids = set(results_w2v.keys()) | set(results_ft.keys()) | set(results_glove.keys())

        # 3. Bangun hasil gabungan dengan skor individual dan rata-rata
        combined_results = []
        for vid in all_verse_ids:
            scores = []
            individual_scores = {}
            
            # Ambil informasi ayat dari salah satu hasil (misal w2v)
            # Jika tidak ada di w2v, coba dari ft, lalu glove
            info = results_w2v.get(vid) or results_ft.get(vid) or results_glove.get(vid)
            if not info:
                continue

            # Kumpulkan skor dari setiap model
            w2v_sim = results_w2v.get(vid, {}).get('similarity', 0.0)
            ft_sim = results_ft.get(vid, {}).get('similarity', 0.0)
            glove_sim = results_glove.get(vid, {}).get('similarity', 0.0)

            individual_scores['word2vec'] = w2v_sim
            individual_scores['fasttext'] = ft_sim
            individual_scores['glove'] = glove_sim
            
            # Hanya sertakan skor > 0 dalam perhitungan rata-rata
            valid_scores = [s for s in [w2v_sim, ft_sim, glove_sim] if s > 0]
            if not valid_scores:
                continue # Lewati jika tidak ada skor valid

            avg_similarity = sum(valid_scores) / len(valid_scores)
            
            # Hanya tambahkan jika rata-rata skor di atas threshold
            if avg_similarity < threshold:
                continue

            combined_results.append({
                'verse_id': vid,
                'surah_number': info['surah_number'],
                'surah_name': info['surah_name'],
                'ayat_number': info['ayat_number'],
                'arabic': info['arabic'],
                'translation': info['translation'],
                'similarity': avg_similarity, # Skor rata-rata
                'individual_scores': individual_scores # Skor dari masing-masing model
            })

        # 4. Urutkan hasil berdasarkan skor rata-rata
        combined_results.sort(key=lambda x: x['similarity'], reverse=True)

        return combined_results[:limit] 