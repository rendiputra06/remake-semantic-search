import time
from flask import jsonify
from backend.db import get_relevant_verses_by_query, add_evaluation_result
from backend.lexical_search import LexicalSearch
from app.api.services.search_service import SearchService
from backend.ensemble_embedding import EnsembleEmbeddingModel

class EvaluationService:
    def __init__(self):
        self.search_service = SearchService()
        self.lexical_search_engine = None
        self._search_cache = {}

    def _get_lexical_engine(self):
        if self.lexical_search_engine is None:
            self.lexical_search_engine = LexicalSearch()
            self.lexical_search_engine.load_index()
        return self.lexical_search_engine

    def _get_cached_search(self, query_text, model_type, result_limit, threshold):
        cache_key = (query_text, model_type, result_limit, threshold)
        return self._search_cache.get(cache_key)

    def _set_cached_search(self, query_text, model_type, result_limit, threshold, results):
        cache_key = (query_text, model_type, result_limit, threshold)
        self._search_cache[cache_key] = results

    def _extract_verse_ref(self, r):
        if 'surah' in r and 'ayat' in r:
            return f"{r['surah']}:{r['ayat']}"
        elif 'surah_id' in r and 'verse_number' in r:
            return f"{r['surah_id']}:{r['verse_number']}"
        elif 'surah_number' in r and 'ayat_number' in r:
            return f"{r['surah_number']}:{r['ayat_number']}"
        return None

    def calculate_metrics(self, found, ground_truth):
        true_positive = len(found & ground_truth)
        false_positive = len(found - ground_truth)
        false_negative = len(ground_truth - found)
        
        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall + 1e-8) if (precision + recall) > 0 else 0
        accuracy = (true_positive) / (true_positive + false_positive + false_negative) if (true_positive + false_positive + false_negative) > 0 else 0
        
        return {
            'true_positive': true_positive,
            'false_positive': false_positive,
            'false_negative': false_negative,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'accuracy': round(accuracy, 4),
            'tp_verses': sorted(list(found & ground_truth)),
            'fp_verses': sorted(list(found - ground_truth)),
            'fn_verses': sorted(list(ground_truth - found))
        }

    def format_eval_result(self, method, label, found, ground_truth, exec_time, threshold=None, additional_info=None):
        metrics = self.calculate_metrics(found, ground_truth)
        result = {
            'method': method,
            'label': label,
            **metrics,
            'exec_time': exec_time,
            'threshold': threshold,
            'total_relevant': len(ground_truth),
            'total_found': len(found),
            'found_verses': sorted(list(found))
        }
        if additional_info:
            result.update(additional_info)
        return result

    def run_full_evaluation(self, query_id, query_text, result_limit, selected_methods, threshold_per_model, ensemble_config):
        # Ground truth
        ayat_relevan = get_relevant_verses_by_query(query_id)
        ground_truth = set([a['verse_ref'] for a in ayat_relevan])
        if not ground_truth:
            return None, "Ayat relevan belum diinput"

        results = []
        
        # 1. Lexical
        if not selected_methods or 'lexical' in selected_methods:
            try:
                start = time.time()
                found = self._get_cached_search(query_text, 'lexical', result_limit, 0.0)
                if found is None:
                    engine = self._get_lexical_engine()
                    lex_results = engine.search(query_text, limit=result_limit)
                    found = set()
                    for r in lex_results if result_limit is None else lex_results[:result_limit]:
                        ref = self._extract_verse_ref(r)
                        if ref: found.add(ref)
                    self._set_cached_search(query_text, 'lexical', result_limit, 0.0, found)
                
                exec_time = round(time.time() - start, 3)
                res = self.format_eval_result('lexical', 'Lexical', found, ground_truth, exec_time, threshold=0.0)
                add_evaluation_result(query_id, 'lexical', res['precision'], res['recall'], res['f1'], exec_time)
                results.append(res)
            except Exception as e:
                results.append({'method': 'lexical', 'label': 'Lexical', 'error': str(e)})

        # 2. Semantic
        for model in ['word2vec', 'fasttext', 'glove']:
            if not selected_methods or model in selected_methods:
                try:
                    start = time.time()
                    threshold = float(threshold_per_model.get(model, 0.5))
                    found = self._get_cached_search(query_text, model, result_limit, threshold)
                    if found is None:
                        res_search = self.search_service.semantic_search(query_text, model, result_limit, threshold)
                        found = set()
                        for r in res_search['results']:
                            ref = self._extract_verse_ref(r)
                            if ref: found.add(ref)
                        self._set_cached_search(query_text, model, result_limit, threshold, found)
                    
                    exec_time = round(time.time() - start, 3)
                    res = self.format_eval_result(model, f'Semantic ({model.capitalize()})', found, ground_truth, exec_time, threshold=threshold)
                    add_evaluation_result(query_id, model, res['precision'], res['recall'], res['f1'], exec_time)
                    results.append(res)
                except Exception as e:
                    results.append({'method': model, 'label': f'Semantic ({model.capitalize()})', 'error': str(e)})

        # 3. Ensemble
        if not selected_methods or 'ensemble' in selected_methods:
            try:
                self.search_service._init_semantic_model('word2vec')
                self.search_service._init_semantic_model('fasttext')
                self.search_service._init_semantic_model('glove')
                
                w2v_model = self.search_service._semantic_models['word2vec']
                ft_model = self.search_service._semantic_models['fasttext']
                glove_model = self.search_service._semantic_models['glove']
                
                ensemble_method = ensemble_config.get('method', 'weighted')
                use_voting_filter = ensemble_config.get('use_voting_filter', False)
                w2v_t = float(ensemble_config.get('w2v_threshold', 0.5))
                ft_t = float(ensemble_config.get('ft_threshold', 0.5))
                gv_t = float(ensemble_config.get('glove_threshold', 0.5))
                bonus = float(ensemble_config.get('voting_bonus', 0.05))
                ensemble_threshold = float(threshold_per_model.get('ensemble', 0.5))

                configs = []
                if ensemble_method in ['weighted', 'all']:
                    configs.append({'name': 'Weighted Averaging', 'key': 'ensemble_weighted', 'use_meta': False, 'vf': use_voting_filter, 't': (w2v_t, ft_t, gv_t), 'b': bonus})
                if ensemble_method in ['voting', 'all']:
                    configs.append({'name': 'Voting', 'key': 'ensemble_voting', 'use_meta': False, 'vf': True, 't': (0.5, 0.5, 0.5), 'b': bonus})
                if ensemble_method in ['meta', 'all']:
                    configs.append({'name': 'Meta-Ensemble', 'key': 'ensemble_meta', 'use_meta': True, 'vf': False, 't': (0.5, 0.5, 0.5), 'b': 0.0})

                for config in configs:
                    try:
                        start = time.time()
                        ensemble = EnsembleEmbeddingModel(
                            w2v_model, ft_model, glove_model,
                            word2vec_threshold=config['t'][0],
                            fasttext_threshold=config['t'][1],
                            glove_threshold=config['t'][2],
                            voting_bonus=config['b'],
                            use_meta_ensemble=config['use_meta'],
                            use_voting_filter=config['vf']
                        )
                        ensemble_results = ensemble.search(query_text, 'id', result_limit, ensemble_threshold)
                        found = set()
                        for r in ensemble_results:
                            ref = self._extract_verse_ref(r)
                            if ref: found.add(ref)
                        
                        exec_time = round(time.time() - start, 3)
                        res = self.format_eval_result(config['key'], f'Ensemble ({config["name"]})', found, ground_truth, exec_time, threshold=ensemble_threshold)
                        add_evaluation_result(query_id, config['key'], res['precision'], res['recall'], res['f1'], exec_time)
                        results.append(res)
                    except Exception as e:
                        results.append({'method': config['key'], 'label': f'Ensemble ({config["name"]})', 'error': str(e)})

            except Exception as e:
                results.append({'method': 'ensemble', 'label': 'Ensemble', 'error': str(e)})

        return results, None
