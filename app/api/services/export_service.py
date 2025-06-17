"""
Export service implementation.
"""
from typing import Dict, List
import pandas as pd
import io
import datetime
import json

class ExportService:
    """Service class for handling export operations."""
    
    def export_to_excel(self, query: str, search_type: str,
                       results: List[Dict], model: str = None,
                       expanded_queries: List[str] = None) -> tuple:
        """Export search results to Excel."""
        try:
            if not results:
                return False, 'No results to export', None
            
            # Set title based on search type
            if search_type == 'semantic':
                title = f"Hasil Pencarian Semantik ({model.upper()}) untuk '{query}'"
            elif search_type == 'lexical':
                title = f"Hasil Pencarian Leksikal untuk '{query}'"
            elif search_type == 'expanded':
                title = f"Hasil Pencarian Semantik dengan Ekspansi Sinonim ({model.upper()}) untuk '{query}'"
            else:
                title = f"Hasil Pencarian untuk '{query}'"
            
            # Create Excel file in memory
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='openpyxl')
            
            # Format data for info sheet
            info_data = {
                'Informasi': [
                    'Query Pencarian',
                    'Tipe Pencarian',
                    'Jumlah Hasil',
                    'Waktu Ekspor'
                ],
                'Nilai': [
                    query,
                    search_type,
                    len(results),
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            # Add expanded queries info if available
            if search_type == 'expanded' and expanded_queries:
                info_data['Informasi'].append('Query Diperluas')
                info_data['Nilai'].append(', '.join(expanded_queries))
            
            # Write info sheet
            info_df = pd.DataFrame(info_data)
            info_df.to_excel(writer, sheet_name='Informasi Pencarian', index=False)
            
            # Format data for results sheet
            results_data = []
            for result in results:
                row = {
                    'Surah': result.get('surah_number'),
                    'Nama Surah': result.get('surah_name'),
                    'Ayat': result.get('ayat_number'),
                    'Referensi': f"{result.get('surah_number')}:{result.get('ayat_number')}",
                    'Teks Arab': result.get('arabic'),
                    'Terjemahan': result.get('translation'),
                }
                
                # Add specific data based on search type
                if 'similarity' in result:
                    row['Skor Kesamaan'] = result.get('similarity')
                    row['Persentase Kesamaan'] = f"{int(result.get('similarity', 0) * 100)}%"
                
                if 'source_query' in result:
                    row['Query Sumber'] = result.get('source_query')
                
                if 'match_type' in result:
                    match_type = result.get('match_type')
                    row['Tipe Kecocokan'] = {
                        'exact_phrase': 'Frasa Persis',
                        'regex': 'Regex'
                    }.get(match_type, 'Kata Kunci')
                
                # Add classification data if available
                if result.get('classification'):
                    row['Kategori'] = result['classification']['title']
                    if 'path' in result['classification']:
                        row['Path Klasifikasi'] = ' > '.join(result['classification']['path'])
                
                results_data.append(row)
            
            # Write results sheet
            df = pd.DataFrame(results_data)
            df.to_excel(writer, sheet_name='Hasil Pencarian', index=False)
            
            # Generate safe filename
            safe_query = ''.join(c if c.isalnum() else '_' for c in query)
            filename = f"Pencarian_{search_type}_{safe_query}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Save and close
            writer.close()
            output.seek(0)
            
            return True, 'Export berhasil', {
                'file': output,
                'filename': filename,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
        except Exception as e:
            return False, f'Error saat mengekspor hasil: {str(e)}', None