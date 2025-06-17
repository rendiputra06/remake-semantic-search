"""
Thesaurus service implementation.
"""
from typing import List, Dict, Optional
from backend.thesaurus import IndonesianThesaurus
import os
import subprocess

class ThesaurusService:
    """Service class for handling thesaurus operations."""
    
    def __init__(self):
        self._thesaurus = None
    
    def _init_thesaurus(self):
        """Initialize thesaurus if not initialized."""
        if not self._thesaurus:
            self._thesaurus = IndonesianThesaurus()
    
    def get_synonyms(self, word: str) -> Dict:
        """Get synonyms for a word."""
        self._init_thesaurus()
        
        synonyms = self._thesaurus.get_synonyms(word)
        return {
            'word': word,
            'synonyms': synonyms,
            'count': len(synonyms)
        }
    
    def add_synonym(self, word: str, synonym: str) -> Dict:
        """Add a synonym for a word."""
        self._init_thesaurus()
        
        success = self._thesaurus.add_synonym(word, synonym)
        return {
            'success': success,
            'message': f'Synonym "{synonym}" added to word "{word}"' if success
                      else 'Failed to add synonym'
        }
    
    def enrich_thesaurus(self, wordlist_name: str, relation_type: str = 'synonym',
                        min_score: float = 0.7, max_relations: int = 5) -> Dict:
        """Enrich thesaurus using wordlist."""
        # Validate wordlist exists
        wordlist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                   '..', '..', '..', 'database', 'wordlists'))
        wordlist_path = os.path.join(wordlist_dir, wordlist_name)
        
        if not os.path.exists(wordlist_path):
            return {
                'success': False,
                'message': f'Wordlist tidak ditemukan: {wordlist_name}'
            }
        
        try:
            # Run enrichment script
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                      '..', '..', '..',
                                                      'scripts/enrich_thesaurus.py'))
            command = [
                'python', script_path,
                '--wordlist', wordlist_path,
                '--type', relation_type,
                '--min-score', str(min_score),
                '--max-relations', str(max_relations)
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Pengayaan tesaurus berhasil',
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'message': 'Error saat menjalankan proses pengayaan',
                    'error': result.stderr
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_word_relations(self, word: str, depth: int = 2) -> Dict:
        """Get word relations for visualization."""
        self._init_thesaurus()
        
        nodes = []
        edges = []
        visited = set()
        
        # Helper function to get relations recursively
        def add_relations(source_id: int, word: str, current_depth: int):
            if current_depth > depth or source_id in visited:
                return
            
            visited.add(source_id)
            
            # Add main node if not exists
            if not any(n['id'] == source_id for n in nodes):
                nodes.append({
                    'id': source_id,
                    'label': word,
                    'group': 'main' if current_depth == 1 else 'related'
                })
            
            # Get all relations
            relations = self._thesaurus.get_all_relations(source_id)
            
            for rel in relations:
                target_id = rel['target_id']
                
                # Add target node if not exists
                if not any(n['id'] == target_id for n in nodes):
                    nodes.append({
                        'id': target_id,
                        'label': rel['word'],
                        'group': rel['type']
                    })
                
                # Add edge if not exists
                edge_id = f"{source_id}-{target_id}"
                if not any(e['id'] == edge_id for e in edges):
                    edges.append({
                        'id': edge_id,
                        'from': source_id,
                        'to': target_id,
                        'label': rel['type'],
                        'type': rel['type'],
                        'strength': rel.get('strength', 1.0)
                    })
                
                # Recurse for next level
                if current_depth < depth:
                    add_relations(target_id, rel['word'], current_depth + 1)
        
        # Get word ID
        word_id = self._thesaurus.get_word_id(word)
        if word_id:
            add_relations(word_id, word, 1)
            
            return {
                'success': True,
                'nodes': nodes,
                'edges': edges
            }
        else:
            return {
                'success': False,
                'message': f'Kata "{word}" tidak ditemukan dalam database'
            }