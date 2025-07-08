import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel
from backend.meta_ensemble import MetaEnsembleModel

def l2_normalize(vec):
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm

def calculate_adaptive_threshold(scores, fallback=0.5):
    if not scores:
        return fallback
    try:
        perc = np.percentile(scores, 75)
        if np.isnan(perc) or perc == 0:
            return fallback
        return perc
    except Exception:
        return fallback

class EnsembleEmbeddingModel:
    """
    Model ensemble untuk menggabungkan Word2Vec, FastText, dan GloVe dengan metode weighted averaging dan voting.
    """
    def __init__(self, 
                 word2vec_model: Word2VecModel, 
                 fasttext_model: FastTextModel, 
                 glove_model: GloVeModel,
                 word2vec_weight: float = 1.0,
                 fasttext_weight: float = 1.0,
                 glove_weight: float = 1.0,
                 voting_bonus: float = 0.05,
                 use_meta_ensemble: bool = False):
        self.word2vec_model = word2vec_model
        self.fasttext_model = fasttext_model
        self.glove_model = glove_model
        self.verse_data = None  # Akan diambil dari salah satu model (diasumsikan sama)
        self.verse_vectors = {}  # vektor ensemble untuk setiap ayat
        self.word2vec_weight = word2vec_weight
        self.fasttext_weight = fasttext_weight
        self.glove_weight = glove_weight
        self.voting_bonus = voting_bonus
        self.use_meta_ensemble = use_meta_ensemble
        self.meta_ensemble = MetaEnsembleModel() if use_meta_ensemble else None
        if use_meta_ensemble:
            try:
                self.meta_ensemble.load_model()
                print("Meta-ensemble model loaded successfully")
            except Exception as e:
                print(f"Meta-ensemble model not available, falling back to weighted ensemble: {e}")
                self.use_meta_ensemble = False

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
            self.verse_vectors[verse_id] = l2_normalize(avg_vec)

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
        return l2_normalize(np.mean(vectors, axis=0))


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
        all_weighted_similarities = []
        query_length = len(query.split())
        for vid in all_verse_ids:
            individual_scores = {}
            info = results_w2v.get(vid) or results_ft.get(vid) or results_glove.get(vid)
            if not info:
                continue
            w2v_sim = results_w2v.get(vid, {}).get('similarity', 0.0)
            ft_sim = results_ft.get(vid, {}).get('similarity', 0.0)
            glove_sim = results_glove.get(vid, {}).get('similarity', 0.0)
            individual_scores['word2vec'] = w2v_sim
            individual_scores['fasttext'] = ft_sim
            individual_scores['glove'] = glove_sim
            # Verse length (approximate)
            verse_length = len(info.get('arabic', '').split()) if info.get('arabic') else 0
            # Calculate ensemble score
            if self.use_meta_ensemble and self.meta_ensemble and self.meta_ensemble.is_trained:
                # Use meta-ensemble prediction
                meta_result = self.meta_ensemble.predict_relevance(
                    w2v_sim, ft_sim, glove_sim, query_length, verse_length
                )
                ensemble_score = meta_result['relevance_score']
                meta_info = {
                    'meta_ensemble_score': ensemble_score,
                    'meta_ensemble_probability': meta_result['relevance_probability'],
                    'meta_ensemble_features': meta_result['features']
                }
            else:
                # Fallback to weighted ensemble
                weights = []
                sims = []
                if w2v_sim > 0:
                    weights.append(self.word2vec_weight)
                    sims.append(w2v_sim)
                if ft_sim > 0:
                    weights.append(self.fasttext_weight)
                    sims.append(ft_sim)
                if glove_sim > 0:
                    weights.append(self.glove_weight)
                    sims.append(glove_sim)
                if not sims:
                    continue
                ensemble_score = sum(w * s for w, s in zip(weights, sims)) / sum(weights)
                # Voting: bonus jika ayat muncul di >=2 model
                model_count = sum([w2v_sim > 0, ft_sim > 0, glove_sim > 0])
                if model_count >= 2:
                    ensemble_score += self.voting_bonus
                meta_info = {'model_count': model_count}
            all_weighted_similarities.append(ensemble_score)
            combined_results.append({
                'verse_id': vid,
                'surah_number': info['surah_number'],
                'surah_name': info['surah_name'],
                'ayat_number': info['ayat_number'],
                'arabic': info['arabic'],
                'translation': info['translation'],
                'similarity': ensemble_score, # Skor ensemble (weighted atau meta-ensemble)
                'individual_scores': individual_scores,
                **meta_info
            })
        # 4. Threshold adaptif jika threshold=None
        use_threshold = threshold
        if threshold is None:
            use_threshold = calculate_adaptive_threshold(all_weighted_similarities, fallback=0.5)
        filtered_results = [r for r in combined_results if r['similarity'] >= use_threshold]
        filtered_results.sort(key=lambda x: x['similarity'], reverse=True)
        return filtered_results[:limit] 