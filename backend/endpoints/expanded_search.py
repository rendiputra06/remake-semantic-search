from flask import jsonify, request, session
from backend.db import get_db_connection, add_search_history
from backend.thesaurus import IndonesianThesaurus
from backend.lexical_search import LexicalSearch
import json
import traceback

# Inisialisasi global objects
thesaurus = None
lexical_search = None

def init_lexical_search():
    """
    Inisialisasi pencarian leksikal
    """
    global lexical_search
    if lexical_search is None:
        try:
            lexical_search = LexicalSearch()
            lexical_search.load_index()
            return lexical_search
        except Exception as e:
            raise Exception(f'Failed to initialize lexical search: {str(e)}')
    return lexical_search

def init_thesaurus():
    """
    Inisialisasi thesaurus
    """
    global thesaurus
    if thesaurus is None:
        try:
            thesaurus = IndonesianThesaurus()
            return thesaurus
        except Exception as e:
            raise Exception(f'Failed to initialize thesaurus: {str(e)}')
    return thesaurus

def get_classification_path(index_id):
    """
    Mendapatkan path klasifikasi untuk suatu index
    """
    path = []
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_id = index_id
    while current_id:
        cursor.execute('SELECT id, title, parent_id FROM quran_index WHERE id = ?', (current_id,))
        index = cursor.fetchone()
        if index:
            path.insert(0, {
                'id': index['id'],
                'title': index['title']
            })
            current_id = index['parent_id']
        else:
            break
    
    conn.close()
    return path

def expanded_search_endpoint():
    """
    Endpoint untuk pencarian leksikal dengan ekspansi query menggunakan sinonim
    """
    # Dapatkan parameter dari request
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    exact_match = data.get('exact_match', False)
    use_regex = data.get('use_regex', False)
    limit = int(data.get('limit', 10))
    
    try:
        # Inisialisasi komponen yang diperlukan
        search_engine = init_lexical_search()
        thesaurus_engine = init_thesaurus()
        
        # Ekspansi query dengan sinonim
        expanded_queries = thesaurus_engine.expand_query(query)
        
        # Lakukan pencarian untuk setiap query yang diperluas
        all_results = []
        
        # Cari untuk setiap query yang diperluas
        for expanded_query in expanded_queries:
            results = search_engine.search(expanded_query, exact_match, use_regex, limit)
            
            # Tambahkan sumber query
            for result in results:
                result['source_query'] = expanded_query
            
            all_results.extend(results)
        
        # Hapus duplikat berdasarkan verse_id
        unique_results = {}
        for result in all_results:
            verse_id = result['verse_id']            # Kalkulasi skor berdasarkan match_type
            score = 0
            if 'match_type' in result:
                if result['match_type'] == 'exact_phrase':
                    score = 1.0
                elif result['match_type'] == 'keywords':
                    score = 0.8
                elif result['match_type'] == 'regex':
                    score = 0.6
            
            # Tambahkan skor ke hasil
            result['score'] = score
                
            # Jika ayat belum ada atau hasil baru memiliki kesamaan lebih tinggi
            if verse_id not in unique_results or result['score'] > unique_results[verse_id]['score']:
                unique_results[verse_id] = result
        
        # Konversi kembali ke list dan urutkan berdasarkan score
        results = list(unique_results.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Batasi jumlah hasil
        results = results[:limit]
        
        # Tambahkan informasi klasifikasi
        for result in results:
            # Dapatkan index_id berdasarkan surah dan ayat
            surah = result['surah_number']
            ayat = result['ayat_number']
            ayat_ref = f"{surah}:{ayat}"
            
            # Cari melalui list_ayat dalam format JSON
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, list_ayat 
                FROM quran_index 
                WHERE list_ayat IS NOT NULL
            ''')
            
            indexes_with_ayat = cursor.fetchall()
            conn.close()
            
            matching_indexes = []
            for idx in indexes_with_ayat:
                if idx['list_ayat']:
                    try:
                        ayat_list = json.loads(idx['list_ayat'])
                        if ayat_list and ayat_ref in ayat_list:
                            matching_indexes.append({
                                'id': idx['id'],
                                'title': idx['title']
                            })
                    except json.JSONDecodeError:
                        continue
            
            if matching_indexes:
                # Pilih klasifikasi pertama untuk breadcrumb path
                primary_classification = matching_indexes[0]
                result['classification'] = {
                    'id': primary_classification['id'],
                    'title': primary_classification['title'],
                    'path': get_classification_path(primary_classification['id'])
                }
                
                # Tambahkan semua klasifikasi terkait
                result['related_classifications'] = matching_indexes
            else:
                result['classification'] = None
                result['related_classifications'] = []
        
        # Tambahkan ke histori pencarian jika user sudah login
        if 'user_id' in session:
            add_search_history(session['user_id'], query, 'expanded_lexical', len(results))
        
        return jsonify({
            'query': query,
            'expanded_queries': expanded_queries,
            'search_type': 'expanded_lexical',
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        print(f"Expanded search error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
