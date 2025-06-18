"""
Thesaurus related routes for the semantic search API.
"""
from flask import Blueprint, request, session
from werkzeug.utils import secure_filename
import os
from marshmallow import ValidationError

from ..utils import create_response, error_response, validation_error_response
from app.api.schemas.thesaurus_admin import (
    ThesaurusEnrichRequest,
    ThesaurusDataImportRequest,
    WordlistDeleteRequest,
    WordlistResponse
)
from app.auth.decorators import admin_required
from app.admin.utils import enrich_thesaurus, import_thesaurus_data
from backend.db import get_db_connection, get_user_by_id
from backend.thesaurus import IndonesianThesaurus

thesaurus_bp = Blueprint('thesaurus', __name__)

# Global thesaurus instance
thesaurus = None

@thesaurus_bp.route('/enrich', methods=['POST'])
@admin_required
def enrich():
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

@thesaurus_bp.route('/import', methods=['POST'])
@admin_required
def import_data():
    """API endpoint for importing thesaurus data from CSV/Excel file."""
    try:
        if 'thesaurus_file' not in request.files:
            return error_response(400, 'File tidak diunggah')
        
        file = request.files['thesaurus_file']
        if file.filename == '':
            return error_response(400, 'Tidak ada file yang dipilih')
        
        # Validate request
        schema = ThesaurusDataImportRequest()
        data = schema.load(request.form)
        
        # Import data
        result = import_thesaurus_data(
            file, 
            data['relation_type'],
            data.get('overwrite', False)
        )
        
        if result.returncode == 0:
            return create_response(
                message='Data tesaurus berhasil diimpor'
            )
        else:
            return error_response(500, result.stderr)
        
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, str(e))

@thesaurus_bp.route('/wordlist/delete', methods=['POST'])
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
            return create_response(
                data={'filename': filename},
                message=f'File {filename} berhasil dihapus'
            )
        else:
            return error_response(404, f'File {filename} tidak ditemukan')
            
    except ValidationError as err:
        return validation_error_response(err.messages)
    except Exception as e:
        return error_response(500, str(e))

@thesaurus_bp.route('/search', methods=['GET'])
def search():
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

@thesaurus_bp.route('/synonyms', methods=['GET'])
def get_synonyms():
    """
    Endpoint untuk mendapatkan sinonim kata
    """
    word = request.args.get('word', '')
    if not word:
        return error_response(400, 'Parameter kata diperlukan')
    
    # Initialize thesaurus if needed
    global thesaurus
    if thesaurus is None:
        try:
            thesaurus = IndonesianThesaurus()
        except Exception as e:
            return error_response(500, f'Gagal menginisialisasi tesaurus: {str(e)}')
    
    # Get synonyms
    try:
        synonyms = thesaurus.get_synonyms(word)
        return create_response(
            data={
                'word': word,
                'synonyms': synonyms,
                'count': len(synonyms)
            },
            message='Sinonim berhasil diambil'
        )
    except Exception as e:
        return error_response(500, str(e))