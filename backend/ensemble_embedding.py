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
                print(f"[Ensemble] Shape mismatch for verse_id {verse_id}: {[v.shape for v in vectors]}")
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
        Melakukan pencarian ensemble dengan metode voting.
        """
        from collections import Counter, defaultdict
        # Ambil hasil pencarian dari masing-masing model
        results_w2v = self.word2vec_model.search(query, language, limit=limit*2, threshold=threshold)
        results_ft = self.fasttext_model.search(query, language, limit=limit*2, threshold=threshold)
        results_glove = self.glove_model.search(query, language, limit=limit*2, threshold=threshold)
        all_results = []
        similarity_map = defaultdict(list)
        verse_info_map = {}
        for res in results_w2v:
            all_results.append(res['verse_id'])
            similarity_map[res['verse_id']].append(res['similarity'])
            verse_info_map[res['verse_id']] = res
        for res in results_ft:
            all_results.append(res['verse_id'])
            similarity_map[res['verse_id']].append(res['similarity'])
            verse_info_map[res['verse_id']] = res
        for res in results_glove:
            all_results.append(res['verse_id'])
            similarity_map[res['verse_id']].append(res['similarity'])
            verse_info_map[res['verse_id']] = res
        # Hitung voting
        vote_counts = Counter(all_results)
        # Urutkan berdasarkan voting dan rata-rata similarity
        sorted_verse_ids = sorted(
            vote_counts.keys(),
            key=lambda vid: (vote_counts[vid], sum(similarity_map[vid])/len(similarity_map[vid])),
            reverse=True
        )
        # Ambil hasil
        final_results = []
        for vid in sorted_verse_ids[:limit]:
            info = verse_info_map[vid]
            final_results.append({
                'verse_id': vid,
                'surah_number': info['surah_number'],
                'surah_name': info['surah_name'],
                'ayat_number': info['ayat_number'],
                'arabic': info['arabic'],
                'translation': info['translation'],
                'similarity': sum(similarity_map[vid])/len(similarity_map[vid]),
                'votes': vote_counts[vid]
            })
        return final_results 