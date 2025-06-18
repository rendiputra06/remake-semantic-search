"""
Public Thesaurus Service for handling public thesaurus operations.
"""
from typing import Dict, List, Optional
from backend.db import get_db_connection
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import random
import time
import functools

class ThesaurusCache:
    """Simple in-memory cache for thesaurus data."""
    
    def __init__(self, ttl: int = 300):  # 5 minutes TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Dict]:
        """Get value from cache if not expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict):
        """Set value in cache with timestamp."""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cached data."""
        self.cache.clear()

def cached_method(func):
    """Decorator for caching method results."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
        
        # Try to get from cache
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute function and cache result
        result = func(self, *args, **kwargs)
        self.cache.set(cache_key, result)
        return result
    return wrapper

class PublicThesaurusService:
    """Service class for handling public thesaurus operations."""
    
    def __init__(self):
        self.cache = ThesaurusCache()
        self.stemmer = StemmerFactory().create_stemmer()
    
    def _get_word_id(self, word: str) -> Optional[int]:
        """Get word ID with stemming fallback like in thesaurus.py."""
        word = word.strip().lower()
        
        try:
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            # Try exact match first
            cursor.execute('SELECT id FROM lexical WHERE word = ?', (word,))
            word_row = cursor.fetchone()
            
            if word_row:
                conn.close()
                return word_row['id']
            
            # If not found, try with stemming (like in thesaurus.py)
            stemmed_word = self.stemmer.stem(word)
            if stemmed_word != word:
                cursor.execute('SELECT id FROM lexical WHERE word = ?', (stemmed_word,))
                word_row = cursor.fetchone()
                
                if word_row:
                    conn.close()
                    return word_row['id']
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting word ID for '{word}': {str(e)}")
            return None
    
    def search_word(self, word: str) -> Dict:
        """Search for a word and return its relations."""
        if not word or len(word.strip()) == 0:
            return {
                'synonyms': [],
                'antonyms': [],
                'hyponyms': [],
                'hypernyms': []
            }
        
        # Use the new _get_word_id method with stemming fallback
        word_id = self._get_word_id(word)
        
        if not word_id:
            return {
                'synonyms': [],
                'antonyms': [],
                'hyponyms': [],
                'hypernyms': []
            }
        
        try:
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            results = {
                'synonyms': [],
                'antonyms': [],
                'hyponyms': [],
                'hypernyms': []
            }
            
            # Get synonyms (has strength column)
            cursor.execute('''
                SELECT l.word, s.strength as score
                FROM synonyms s
                JOIN lexical l ON s.synonym_id = l.id
                WHERE s.word_id = ?
                ORDER BY s.strength DESC
            ''', (word_id,))
            
            for row in cursor.fetchall():
                results['synonyms'].append({
                    'word': row['word'],
                    'score': row['score']
                })
            
            # Get antonyms (has strength column)
            cursor.execute('''
                SELECT l.word, a.strength as score
                FROM antonyms a
                JOIN lexical l ON a.antonym_id = l.id
                WHERE a.word_id = ?
                ORDER BY a.strength DESC
            ''', (word_id,))
            
            for row in cursor.fetchall():
                results['antonyms'].append({
                    'word': row['word'],
                    'score': row['score']
                })
            
            # Get hyponyms (no strength column, use default score 1.0)
            cursor.execute('''
                SELECT l.word, 1.0 as score
                FROM hyponyms h
                JOIN lexical l ON h.hyponym_id = l.id
                WHERE h.word_id = ?
                ORDER BY l.word
            ''', (word_id,))
            
            for row in cursor.fetchall():
                results['hyponyms'].append({
                    'word': row['word'],
                    'score': row['score']
                })
            
            # Get hypernyms (no strength column, use default score 1.0)
            cursor.execute('''
                SELECT l.word, 1.0 as score
                FROM hypernyms h
                JOIN lexical l ON h.hypernym_id = l.id
                WHERE h.word_id = ?
                ORDER BY l.word
            ''', (word_id,))
            
            for row in cursor.fetchall():
                results['hypernyms'].append({
                    'word': row['word'],
                    'score': row['score']
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching word '{word}': {str(e)}")
            return {
                'synonyms': [],
                'antonyms': [],
                'hyponyms': [],
                'hypernyms': []
            }
    
    @cached_method
    def browse_words(self, page: int = 1, per_page: int = 20, 
                    sort_by: str = 'word', filter_type: str = 'all') -> Dict:
        """Browse words with pagination and filtering."""
        try:
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            # Validate parameters
            page = max(1, page)
            per_page = max(1, min(100, per_page))  # Limit per_page to 100
            
            # Build query based on filter
            if filter_type == 'all':
                # Count total words
                cursor.execute('SELECT COUNT(*) as total FROM lexical')
                total = cursor.fetchone()['total']
                
                # Get words with pagination
                offset = (page - 1) * per_page
                
                if sort_by == 'word':
                    cursor.execute('''
                        SELECT id, word, definition, example
                        FROM lexical
                        ORDER BY word
                        LIMIT ? OFFSET ?
                    ''', (per_page, offset))
                else:
                    # For other sort types, we need to join with relation tables
                    cursor.execute('''
                        SELECT l.id, l.word, l.definition, l.example
                        FROM lexical l
                        ORDER BY l.word
                        LIMIT ? OFFSET ?
                    ''', (per_page, offset))
            else:
                # Filter by relation type
                relation_table = f"{filter_type}s"  # synonyms, antonyms, etc.
                
                # Count words with this relation type
                cursor.execute(f'''
                    SELECT COUNT(DISTINCT l.id) as total
                    FROM lexical l
                    JOIN {relation_table} r ON l.id = r.word_id
                ''')
                total = cursor.fetchone()['total']
                
                # Get words with this relation type
                offset = (page - 1) * per_page
                cursor.execute(f'''
                    SELECT DISTINCT l.id, l.word, l.definition, l.example
                    FROM lexical l
                    JOIN {relation_table} r ON l.id = r.word_id
                    ORDER BY l.word
                    LIMIT ? OFFSET ?
                ''', (per_page, offset))
            
            words = []
            for row in cursor.fetchall():
                # Get relation count for this word
                cursor.execute('''
                    SELECT 
                        (SELECT COUNT(*) FROM synonyms WHERE word_id = ?) as synonym_count,
                        (SELECT COUNT(*) FROM antonyms WHERE word_id = ?) as antonym_count,
                        (SELECT COUNT(*) FROM hyponyms WHERE word_id = ?) as hyponym_count,
                        (SELECT COUNT(*) FROM hypernyms WHERE word_id = ?) as hypernym_count
                ''', (row['id'], row['id'], row['id'], row['id']))
                
                rel_counts = cursor.fetchone()
                total_relations = (rel_counts['synonym_count'] + rel_counts['antonym_count'] + 
                                 rel_counts['hyponym_count'] + rel_counts['hypernym_count'])
                
                words.append({
                    'id': row['id'],
                    'word': row['word'],
                    'definition': row['definition'],
                    'example': row['example'],
                    'relation_count': total_relations
                })
            
            conn.close()
            
            return {
                'words': words,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            print(f"Error browsing words: {str(e)}")
            return {
                'words': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0
                }
            }
    
    @cached_method
    def get_statistics(self) -> Dict:
        """Get thesaurus statistics."""
        try:
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('SELECT COUNT(*) as total_words FROM lexical')
            total_words = cursor.fetchone()['total_words']
            
            # Get relation counts
            cursor.execute('SELECT COUNT(*) as total_synonyms FROM synonyms')
            total_synonyms = cursor.fetchone()['total_synonyms']
            
            cursor.execute('SELECT COUNT(*) as total_antonyms FROM antonyms')
            total_antonyms = cursor.fetchone()['total_antonyms']
            
            cursor.execute('SELECT COUNT(*) as total_hyponyms FROM hyponyms')
            total_hyponyms = cursor.fetchone()['total_hyponyms']
            
            cursor.execute('SELECT COUNT(*) as total_hypernyms FROM hypernyms')
            total_hypernyms = cursor.fetchone()['total_hypernyms']
            
            total_relations = total_synonyms + total_antonyms + total_hyponyms + total_hypernyms
            
            # Get average strength (only from synonyms and antonyms)
            cursor.execute('SELECT AVG(strength) as avg_strength FROM synonyms')
            avg_synonym_strength = cursor.fetchone()['avg_strength'] or 0.0
            
            cursor.execute('SELECT AVG(strength) as avg_strength FROM antonyms')
            avg_antonym_strength = cursor.fetchone()['avg_strength'] or 0.0
            
            # Calculate overall average (hyponyms and hypernyms have default 1.0)
            total_strength_relations = total_synonyms + total_antonyms
            if total_strength_relations > 0:
                avg_strength = ((avg_synonym_strength * total_synonyms) + 
                              (avg_antonym_strength * total_antonyms)) / total_strength_relations
            else:
                avg_strength = 0.0
            
            # Get top words by relation count
            cursor.execute('''
                SELECT l.word, 
                       (SELECT COUNT(*) FROM synonyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM antonyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM hyponyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM hypernyms WHERE word_id = l.id) as relation_count
                FROM lexical l
                ORDER BY relation_count DESC
                LIMIT 10
            ''')
            
            top_words = []
            for row in cursor.fetchall():
                if row['relation_count'] > 0:
                    top_words.append({
                        'word': row['word'],
                        'relation_count': row['relation_count']
                    })
            
            conn.close()
            
            return {
                'basic_stats': {
                    'unique_words': total_words,
                    'total_relations': total_relations,
                    'avg_score': round(avg_strength, 2)
                },
                'relation_distribution': [
                    {'relation_type': 'synonym', 'count': total_synonyms},
                    {'relation_type': 'antonym', 'count': total_antonyms},
                    {'relation_type': 'hyponym', 'count': total_hyponyms},
                    {'relation_type': 'hypernym', 'count': total_hypernyms}
                ],
                'top_words': top_words
            }
            
        except Exception as e:
            print(f"Error getting statistics: {str(e)}")
            return {
                'basic_stats': {
                    'unique_words': 0,
                    'total_relations': 0,
                    'avg_score': 0.0
                },
                'relation_distribution': [],
                'top_words': []
            }
    
    def get_random_words(self, count: int = 10) -> List[Dict]:
        """Get random words from thesaurus."""
        try:
            count = max(1, min(50, count))  # Limit count to 50
            
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT word
                FROM lexical
                ORDER BY RANDOM()
                LIMIT ?
            ''', (count,))
            
            words = [{'word': row['word']} for row in cursor.fetchall()]
            conn.close()
            
            return words
            
        except Exception as e:
            print(f"Error getting random words: {str(e)}")
            return []
    
    def get_popular_words(self, limit: int = 20) -> List[Dict]:
        """Get popular words (most relations)."""
        try:
            limit = max(1, min(100, limit))  # Limit to 100
            
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT l.word, 
                       (SELECT COUNT(*) FROM synonyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM antonyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM hyponyms WHERE word_id = l.id) +
                       (SELECT COUNT(*) FROM hypernyms WHERE word_id = l.id) as relation_count
                FROM lexical l
                HAVING relation_count > 0
                ORDER BY relation_count DESC
                LIMIT ?
            ''', (limit,))
            
            words = []
            for row in cursor.fetchall():
                words.append({
                    'word': row['word'],
                    'relation_count': row['relation_count']
                })
            
            conn.close()
            
            return words
            
        except Exception as e:
            print(f"Error getting popular words: {str(e)}")
            return []
    
    def search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial word match."""
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            query = query.strip().lower()
            limit = max(1, min(20, limit))
            
            # Use 'thesaurus' to connect to lexical.db
            conn = get_db_connection('thesaurus')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT word
                FROM lexical
                WHERE word LIKE ?
                ORDER BY word
                LIMIT ?
            ''', (f"{query}%", limit))
            
            suggestions = [row['word'] for row in cursor.fetchall()]
            conn.close()
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting search suggestions: {str(e)}")
            return [] 