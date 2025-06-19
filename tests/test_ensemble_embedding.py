import numpy as np
from backend.ensemble_embedding import EnsembleEmbeddingModel
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel

class DummyModel:
    def __init__(self, dim=3):
        self.verse_vectors = {'1': np.ones(dim), '2': np.ones(dim) * 2}
        self.verse_data = {
            '1': {'surah_number': 1, 'surah_name': 'Al-Fatihah', 'ayat_number': 1, 'arabic': '...', 'translation': '...'},
            '2': {'surah_number': 1, 'surah_name': 'Al-Fatihah', 'ayat_number': 2, 'arabic': '...', 'translation': '...'}
        }
    def load_model(self):
        pass
    def load_verse_vectors(self):
        pass
    def _calculate_verse_vector(self, tokens):
        return np.ones(3)

def test_ensemble_initialization_and_averaging():
    w2v = DummyModel()
    ft = DummyModel()
    gv = DummyModel()
    ensemble = EnsembleEmbeddingModel(w2v, ft, gv)
    ensemble.load_models()
    ensemble.load_verse_vectors()
    assert '1' in ensemble.verse_vectors
    assert np.allclose(ensemble.verse_vectors['1'], np.ones(3))
    assert '2' in ensemble.verse_vectors
    assert np.allclose(ensemble.verse_vectors['2'], np.ones(3) * 2)

def test_ensemble_query_vector():
    w2v = DummyModel()
    ft = DummyModel()
    gv = DummyModel()
    ensemble = EnsembleEmbeddingModel(w2v, ft, gv)
    tokens = ['dummy']
    vec = ensemble._calculate_query_vector(tokens)
    assert np.allclose(vec, np.ones(3))

def test_ensemble_search():
    w2v = DummyModel()
    ft = DummyModel()
    gv = DummyModel()
    ensemble = EnsembleEmbeddingModel(w2v, ft, gv)
    ensemble.load_models()
    ensemble.load_verse_vectors()
    results = ensemble.search('dummy', limit=1, threshold=0.0)
    assert len(results) == 1
    assert results[0]['verse_id'] in ['1', '2']
    assert 'similarity' in results[0] 