"""
API routes.
"""
from flask import jsonify, request
from werkzeug.utils import secure_filename
import os
import sqlite3
from marshmallow import ValidationError
import json

from . import api_bp
from .utils import create_response, error_response, validation_error_response
from .schemas_main import (
    ThesaurusEnrichRequest, ThesaurusEnrichResponse,
    QuranIndexImportRequest, QuranIndexTreeResponse,
    StatisticsResponse, LexicalDataImportRequest,
    ThesaurusDataImportRequest, WordlistDeleteRequest,
    WordlistResponse, ThesaurusSearchResponse,
    ThesaurusSearchResults
)
from app.auth.decorators import admin_required
from app.admin.utils import (
    enrich_thesaurus, import_lexical_data,
    import_thesaurus_data
)
from backend.db import get_db_connection, add_relevant_verse, add_relevant_verses_batch
from backend.excel_importer import excel_to_hierarchy_db

@api_bp.route('/thesaurus/enrich', methods=['POST'])
@admin_required
def thesaurus_enrich():
    """API endpoint for thesaurus enrichment using wordlist."""
    try:
        # Validate request
        schema = ThesaurusEnrichRequest()
        data = schema.load(request.form)
        
        # Execute enrichment
        result = enrich_thesaurus(
            data['wordlist'],
            data['relation_type'],
            data['min_score'],
            data['max_relations']
        )
        
        if result.returncode == 0:
            return create_response(
                data={'output': result.stdout},
                message='Pengayaan tesaurus berhasil'
            )
        else:
            return error_response(500, result.stderr)
            
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, str(e))

@api_bp.route('/thesaurus/visualize')
@admin_required
def thesaurus_visualize():
    """API untuk visualisasi tesaurus (dipindahkan dari run.py)."""
    word = request.args.get('word')
    depth = int(request.args.get('depth', 2))
    if not word:
        return jsonify({'success': False, 'message': 'Parameter kata harus disediakan'})

    try:
        # Koneksi ke database lexical bawaan
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'lexical.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Cari ID kata
        cursor.execute("SELECT id FROM lexical WHERE word = ?", (word,))
        word_result = cursor.fetchone()
        if not word_result:
            return jsonify({'success': False, 'message': f'Kata "{word}" tidak ditemukan dalam database'})

        word_id = word_result['id']
        nodes = []
        edges = []

        # Tambahkan node utama
        nodes.append({'id': word_id, 'label': word, 'group': 'main'})

        def get_relations(source_id, current_depth, max_depth):
            if current_depth > max_depth:
                return

            # Sinonim
            cursor.execute(
                """
                SELECT l.id, l.word, s.strength, 'synonym' as type
                FROM synonyms s
                JOIN lexical l ON s.synonym_id = l.id
                WHERE s.word_id = ?
                """,
                (source_id,)
            )
            synonyms = cursor.fetchall()

            # Antonim
            cursor.execute(
                """
                SELECT l.id, l.word, a.strength, 'antonym' as type
                FROM antonyms a
                JOIN lexical l ON a.antonym_id = l.id
                WHERE a.word_id = ?
                """,
                (source_id,)
            )
            antonyms = cursor.fetchall()

            # Hiponim
            cursor.execute(
                """
                SELECT l.id, l.word, 1.0 as strength, 'hyponym' as type
                FROM hyponyms h
                JOIN lexical l ON h.hyponym_id = l.id
                WHERE h.word_id = ?
                """,
                (source_id,)
            )
            hyponyms = cursor.fetchall()

            # Hipernim
            cursor.execute(
                """
                SELECT l.id, l.word, 1.0 as strength, 'hypernym' as type
                FROM hypernyms h
                JOIN lexical l ON h.hypernym_id = l.id
                WHERE h.word_id = ?
                """,
                (source_id,)
            )
            hypernyms = cursor.fetchall()

            all_relations = synonyms + antonyms + hyponyms + hypernyms

            for relation in all_relations:
                target_id = relation['id']

                # Node
                if not any(node['id'] == target_id for node in nodes):
                    nodes.append({'id': target_id, 'label': relation['word'], 'group': relation['type']})

                # Edge
                edge_id = f"{source_id}-{target_id}"
                if not any(edge['id'] == edge_id for edge in edges):
                    edges.append({
                        'id': edge_id,
                        'from': source_id,
                        'to': target_id,
                        'label': relation['type'],
                        'type': relation['type'],
                        'strength': relation['strength']
                    })

                if current_depth < max_depth:
                    get_relations(target_id, current_depth + 1, max_depth)

        get_relations(word_id, 1, depth)

        return jsonify({'success': True, 'nodes': nodes, 'edges': edges})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

@api_bp.route('/quran/index/roots')
@admin_required
def quran_index_roots():
    """API endpoint for getting root Quran indices."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, level FROM quran_index 
            WHERE parent_id IS NULL 
            ORDER BY title
        ''')
        roots = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(root) for root in roots]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/quran/index/tree')
@admin_required
def quran_index_tree():
    """API endpoint for getting the full Quran index tree."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        def get_children(parent_id=None, level=0):
            cursor.execute('''
                SELECT id, title, level, 
                       (SELECT COUNT(*) FROM quran_index qi2 WHERE qi2.parent_id = qi1.id) as child_count 
                FROM quran_index qi1
                WHERE parent_id {} ?
                ORDER BY title
            '''.format('IS' if parent_id is None else '='), (parent_id,))
            
            items = cursor.fetchall()
            result = []
            
            for item in items:
                item_dict = dict(item)
                item_dict['has_children'] = item_dict['child_count'] > 0
                if item_dict['has_children']:
                    item_dict['children'] = get_children(item['id'], level + 1)
                result.append(item_dict)
            
            return result
        
        tree = get_children()
        conn.close()
        
        return create_response(
            data=tree,
            message='Struktur indeks berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, str(e))

@api_bp.route('/quran/index/import-excel', methods=['POST'])
@admin_required
def quran_index_import_excel():
    """API endpoint for importing Quran index from Excel."""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate request data
        schema = QuranIndexImportRequest()
        data = schema.load(request.form)
        
        # Save file temporarily
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)
          # Import Excel data
        success, message = excel_to_hierarchy_db(
            file_path,
            data['sheet_name'],
            data.get('parent_id')
        )
          # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/statistics')
@admin_required
def statistics():
    """API endpoint for getting admin statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get category statistics
        cursor.execute('SELECT COUNT(*) as total FROM quran_index')
        total_categories = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM quran_index WHERE parent_id IS NULL')
        root_categories = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(DISTINCT qi.id) as total 
            FROM quran_index qi 
            INNER JOIN ayat_index ai ON qi.id = ai.index_id
        ''')
        categories_with_ayat = cursor.fetchone()['total']
        
        # Get total verses
        cursor.execute('SELECT COUNT(*) as total FROM ayat_index')
        total_verses = cursor.fetchone()['total']
        
        # Get level statistics
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM quran_index 
            GROUP BY level 
            ORDER BY level
        ''')
        level_stats = cursor.fetchall()
        
        # Get surah statistics
        cursor.execute('''
            SELECT s.id as surah_id, COUNT(*) as ayat_count 
            FROM ayat_index ai 
            INNER JOIN surah s ON ai.surah_id = s.id 
            GROUP BY s.id 
            ORDER BY s.id
        ''')
        surah_stats = cursor.fetchall()
        
        conn.close()
        
        return create_response(
            data={
                'total_categories': total_categories,
                'root_categories': root_categories,
                'categories_with_ayat': categories_with_ayat,
                'total_verses': total_verses,
                'level_stats': [dict(stat) for stat in level_stats],
                'surah_stats': [dict(stat) for stat in surah_stats]
            },
            message='Statistik berhasil diambil'
        )
        
    except Exception as e:
        return error_response(500, str(e))

@api_bp.route('/lexical/import', methods=['POST'])
@admin_required
def lexical_data_import():
    """API endpoint for importing lexical data from CSV/Excel file."""
    try:
        if 'lexical_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['lexical_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate request
        schema = LexicalDataImportRequest()
        data = schema.load(request.form)
        
        # Import data
        result = import_lexical_data(file, data.get('overwrite', False))
        
        return jsonify({
            'success': result.returncode == 0,
            'message': 'Lexical data imported successfully' if result.returncode == 0 else f'Error: {result.stderr}'
        })
        
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/thesaurus/import', methods=['POST'])
@admin_required
def thesaurus_data_import():
    """API endpoint for importing thesaurus data from CSV/Excel file."""
    try:
        if 'thesaurus_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['thesaurus_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate request
        schema = ThesaurusDataImportRequest()
        data = schema.load(request.form)
        
        # Import data
        result = import_thesaurus_data(
            file, 
            data['relation_type'],
            data.get('overwrite', False)
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'message': 'Thesaurus data imported successfully' if result.returncode == 0 else f'Error: {result.stderr}'
        })
        
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/wordlist/delete', methods=['POST'])
@admin_required
def delete_wordlist():
    """Delete a wordlist file."""
    try:
        # Validate request
        schema = WordlistDeleteRequest()
        data = schema.load(request.form)
        filename = data['filename']
        
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
        file_path = os.path.join(wordlist_dir, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            response = {
                'success': True,
                'message': f'File {filename} deleted successfully',
                'filename': filename
            }
        else:
            response = {
                'success': False,
                'message': f'File {filename} not found',
                'filename': filename
            }
            
        schema = WordlistResponse()
        return jsonify(schema.dump(response))
            
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@api_bp.route('/thesaurus/search')
@admin_required
def thesaurus_search():
    """API endpoint for searching thesaurus data."""
    try:
        word = request.args.get('word')
        if not word:
            return error_response(400, 'Kata pencarian diperlukan')

        conn = get_db_connection('thesaurus')
        cursor = conn.cursor()
        
        # Find relations for the word
        cursor.execute('''
            SELECT r.relation_type, r.target_word, r.source_word, r.score 
            FROM thesaurus_relations r
            WHERE r.source_word = ? OR r.target_word = ?
            ORDER BY r.score DESC
        ''', (word, word))
        relations = cursor.fetchall()
        conn.close()

        # Group relations by type
        results = {
            'synonyms': [],
            'antonyms': [],
            'hyponyms': [],
            'hypernyms': []
        }
        
        for rel in relations:
            rel_dict = dict(rel)
            rel_type = rel_dict['relation_type']
            target = rel_dict['target_word']
            source = rel_dict['source_word']
            score = rel_dict['score']
            
            # Add to appropriate group
            if rel_type in results:
                related_word = target if source == word else source
                results[rel_type].append({
                    'word': related_word,
                    'score': score
                })
        
        return create_response(
            data={'results': results},
            message='Pencarian tesaurus berhasil'
        )
        
    except Exception as e:
        return error_response(500, str(e))

@api_bp.route('/import-ayat-excel', methods=['POST'])
@admin_required
def import_ayat_excel():
    """
    Import ayat relevan dari data Excel (frontend kirim list ayat).
    Format request: { ayat: ["2:255", "1:1", ...], query_id: <id> }
    """
    try:
        data = request.get_json()
        ayat_list = data.get('ayat', [])
        query_id = data.get('query_id')
        if not ayat_list or not isinstance(ayat_list, list):
            return jsonify({'success': False, 'message': 'Data ayat tidak valid.'}), 400
        if not query_id:
            return jsonify({'success': False, 'message': 'Query ID wajib dipilih.'}), 400
        # Gunakan batch insert agar lebih cepat
        success, result = add_relevant_verses_batch(query_id, ayat_list)
        if success:
            return jsonify({'success': True, 'message': f'{result} ayat berhasil diimport.'})
        else:
            return jsonify({'success': False, 'message': result}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
