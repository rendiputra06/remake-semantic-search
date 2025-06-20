"""
Export related routes for the semantic search API.
"""
from flask import Blueprint, jsonify, request, send_file
from ..utils import create_response, error_response
import json
import datetime
import pandas as pd
import io
import os

export_bp = Blueprint('export', __name__)

@export_bp.route('/excel', methods=['POST'])
def export_excel():
    """
    Ekspor hasil pencarian ke Excel
    """
    try:
        # Get parameters from request
        query = request.form.get('query', '')
        search_type = request.form.get('searchType', '')
        data_json = request.form.get('data', '')
        
        if not data_json:
            return error_response(400, 'Data tidak diberikan')
        
        # Parse JSON data
        data = json.loads(data_json)
        results = data.get('results', [])
        
        if not results:
            return error_response(400, 'Tidak ada hasil untuk diekspor')
            
        # Create dataframe from search results
        df_data = []
        
        # Set title based on search type
        if search_type == 'semantic':
            model_type = data.get('model', 'word2vec')
            title = f"Hasil Pencarian Semantik ({model_type.upper()}) untuk '{query}'"
        elif search_type == 'lexical':
            title = f"Hasil Pencarian Leksikal untuk '{query}'"
        elif search_type == 'expanded':
            model_type = data.get('model', 'word2vec')
            title = f"Hasil Pencarian Semantik dengan Ekspansi Sinonim ({model_type.upper()}) untuk '{query}'"
        else:
            title = f"Hasil Pencarian untuk '{query}'"
            
        # Format data for Excel
        for i, result in enumerate(results):
            row = {
                'Peringkat': i + 1,
                'Surah': result.get('surah_number'),
                'Nama Surah': result.get('surah_name'),
                'Ayat': result.get('ayat_number'),
                'Referensi': f"{result.get('surah_number')}:{result.get('ayat_number')}",
                'Teks Arab': result.get('arabic'),
                'Terjemahan': result.get('translation'),
            }
            
            # Add specific data based on search type
            if search_type == 'semantic':
                model_type = data.get('model', '').lower()
                row['Skor Kesamaan'] = result.get('similarity')

                if model_type == 'ensemble' and 'individual_scores' in result:
                    # Ganti nama kolom dan tambahkan skor individual
                    row['Skor Rata-rata (Ensemble)'] = row.pop('Skor Kesamaan')
                    row['Skor Word2Vec'] = result['individual_scores'].get('word2vec')
                    row['Skor FastText'] = result['individual_scores'].get('fasttext')
                    row['Skor GloVe'] = result['individual_scores'].get('glove')
                else:
                    row['Persentase Kesamaan'] = f"{int(result.get('similarity', 0) * 100)}%"

            if 'source_query' in result:
                row['Query Sumber'] = result.get('source_query')
                
            if 'match_type' in result:
                match_type = result.get('match_type')
                if match_type == 'exact_phrase':
                    row['Tipe Kecocokan'] = 'Frasa Persis'
                elif match_type == 'regex':
                    row['Tipe Kecocokan'] = 'Regex'
                else:
                    row['Tipe Kecocokan'] = 'Kata Kunci'
            
            # Add classification data if available
            if result.get('classification'):
                row['Kategori'] = result['classification']['title']
                if 'path' in result['classification']:
                    row['Path Klasifikasi'] = ' > '.join(result['classification']['path'])
            
            df_data.append(row)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        # Gunakan context manager agar file tidak korup
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Create info sheet
            info_data = {
                'Informasi': ['Query Pencarian', 'Tipe Pencarian', 'Jumlah Hasil', 'Waktu Ekspor'],
                'Nilai': [
                    query,
                    search_type,
                    len(results),
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }

            if search_type == 'semantic':
                info_data['Informasi'].extend(['Model', 'Durasi Pencarian (detik)', 'Threshold'])
                info_data['Nilai'].extend([
                    data.get('model', 'N/A'),
                    data.get('execution_time', 'N/A'),
                    data.get('threshold', 'N/A')
                ])

            info_df = pd.DataFrame(info_data)
            
            # Add expanded queries info if available
            if search_type == 'expanded' and 'expanded_queries' in data:
                expanded_queries = ', '.join(data['expanded_queries'])
                new_row = pd.DataFrame({
                    'Informasi': ['Query Diperluas'],
                    'Nilai': [expanded_queries]
                })
                info_df = pd.concat([info_df, new_row], ignore_index=True)
            info_df.to_excel(writer, sheet_name='Informasi Pencarian', index=False)

            # Write main results sheet
            df = pd.DataFrame(df_data)
            df.to_excel(writer, sheet_name='Hasil Pencarian', index=False)

        # Pastikan pointer file di awal
        output.seek(0)
        
        # Set safe filename
        safe_query = ''.join(c if c.isalnum() else '_' for c in query)
        filename = f"Pencarian_{search_type}_{safe_query}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Send file to client
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return error_response(500, f'Error saat mengekspor data: {str(e)}')