"""
Helper functions and utilities for admin features.
"""
import os
import json
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename

def get_db_status():
    """Get status of various databases and models."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Model status
    model_status = {}
    for model_name in ['qa_model', 'semantic_model', 'search_model']:
        model_status[model_name] = {
            'initialized': True,  # Replace with actual status check
            'last_updated': '2023-01-01 00:00:00'  # Replace with actual timestamp
        }
    
    # Lexical database status
    lexical_status = {
        'initialized': False,
        'last_updated': None,
        'entry_count': 0
    }
    
    try:
        lexical_status_file = os.path.join(root_dir, 'database', 'lexical_status.json')
        if os.path.exists(lexical_status_file):
            with open(lexical_status_file, 'r') as f:
                lexical_status = json.load(f)
    except:
        pass
    
    # Thesaurus status
    thesaurus_status = {
        'initialized': False,
        'last_updated': None,
        'word_count': 0,
        'relation_count': 0
    }
    
    try:
        thesaurus_status_file = os.path.join(root_dir, 'database', 'thesaurus_status.json')
        if os.path.exists(thesaurus_status_file):
            with open(thesaurus_status_file, 'r') as f:
                thesaurus_status = json.load(f)
    except:
        pass
    
    return model_status, lexical_status, thesaurus_status

def get_wordlist_files():
    """Get list of available wordlist files."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
    wordlist_files = []
    
    if os.path.exists(wordlist_dir):
        for file in os.listdir(wordlist_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(wordlist_dir, file)
                file_size = os.path.getsize(file_path)
                file_created = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Format file size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                wordlist_files.append({
                    'name': file,
                    'size': size_str,
                    'created': file_created,
                    'filename': file  # Added for compatibility with templates
                })
    
    return wordlist_files

def run_lexical_command(command):
    """Run lexical database related commands."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    valid_commands = {
        'init_lexical': ['scripts/init_lexical.py', '--component=lexical'],
        'init_thesaurus': ['scripts/init_lexical.py', '--component=thesaurus'],
        'export_lexical': ['scripts/export_lexical.py', '--type=lexical'],
        'export_thesaurus': ['scripts/export_lexical.py', '--type=all_relations']
    }
    
    if command not in valid_commands:
        raise ValueError(f'Invalid command: {command}')
    
    script_args = valid_commands[command]
    script_path = os.path.abspath(os.path.join(root_dir, script_args[0]))
    
    cmd = ['python', script_path]
    if len(script_args) > 1:
        cmd.extend(script_args[1:])
    
    return subprocess.run(cmd, capture_output=True, text=True)

def run_wordlist_generator(output_filename, min_word_length, min_word_freq, stem_words=False, 
                         use_quran_dataset=False, use_custom_txt=False, custom_txt_files=None):
    """Run wordlist generator with given parameters."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
    os.makedirs(wordlist_dir, exist_ok=True)
    
    output_path = os.path.join(wordlist_dir, output_filename)
    script_path = os.path.abspath(os.path.join(root_dir, 'scripts/wordlist_generator.py'))
    
    # Setup command
    cmd = [
        'python', script_path,
        '--output', output_path,
        '--min-length', str(min_word_length),
        '--min-freq', str(min_word_freq)
    ]
    
    # Process custom text files
    custom_txt_paths = []
    if use_custom_txt and custom_txt_files:
        temp_dir = os.path.join(root_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        for file in custom_txt_files:
            if file and file.filename:
                file_path = os.path.join(temp_dir, secure_filename(file.filename))
                file.save(file_path)
                custom_txt_paths.append(file_path)
    
    if stem_words:
        cmd.append('--stem')
    
    if use_quran_dataset:
        dataset_dir = os.path.join(root_dir, 'dataset')
        cmd.extend(['--quran-dataset', dataset_dir])
    
    if custom_txt_paths:
        cmd.extend(['--input-dir', os.path.dirname(custom_txt_paths[0])])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup temporary files
    for path in custom_txt_paths:
        if os.path.exists(path):
            os.remove(path)
    
    return result

def import_lexical_data(file, overwrite=False):
    """Import lexical data from CSV/Excel file."""
    if not file or not file.filename:
        raise ValueError('No file provided')
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    temp_dir = os.path.join(root_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(file_path)
    
    # Run import script
    script_path = os.path.abspath(os.path.join(root_dir, 'scripts/import_lexical.py'))
    cmd = ['python', script_path, file_path]
    
    if overwrite:
        cmd.append('--overwrite')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return result

def import_thesaurus_data(file, relation_type='synonym', overwrite=False):
    """Import thesaurus data from CSV/Excel file."""
    if not file or not file.filename:
        raise ValueError('No file provided')
    
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    temp_dir = os.path.join(root_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(file_path)
    
    # Run import script
    script_path = os.path.abspath(os.path.join(root_dir, 'scripts/import_thesaurus.py'))
    cmd = [
        'python', script_path,
        '--file', file_path,
        '--type', relation_type
    ]
    
    if overwrite:
        cmd.append('--overwrite')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return result

def enrich_thesaurus(wordlist_name, relation_type='synonym', min_score=0.7, max_relations=5):
    """Enrich thesaurus using wordlist."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    wordlist_dir = os.path.join(root_dir, 'database', 'wordlists')
    wordlist_path = os.path.join(wordlist_dir, wordlist_name)
    
    if not os.path.exists(wordlist_path):
        raise ValueError(f'Wordlist not found: {wordlist_name}')
    
    script_path = os.path.abspath(os.path.join(root_dir, 'scripts/enrich_thesaurus.py'))
    cmd = [
        'python', script_path,
        '--wordlist', wordlist_path,
        '--type', relation_type,
        '--min-score', str(min_score),
        '--max-relations', str(max_relations)
    ]
    
    return subprocess.run(cmd, capture_output=True, text=True)
