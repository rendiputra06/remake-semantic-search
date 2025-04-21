"""
Script untuk melakukan evaluasi kualitatif dengan pakar
"""
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.glove_model import GloVeModel

def load_models():
    """
    Memuat model Word2Vec, FastText, dan GloVe beserta vektor ayat yang sudah disimpan
    """
    print("Memuat model Word2Vec...")
    word2vec_model = Word2VecModel()
    word2vec_vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/word2vec_verses.pkl')
    word2vec_model.load_model()
    word2vec_model.load_verse_vectors(word2vec_vectors_path)
    
    print("Memuat model FastText...")
    fasttext_model = FastTextModel()
    fasttext_vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/fasttext_verses.pkl')
    fasttext_model.load_model()
    fasttext_model.load_verse_vectors(fasttext_vectors_path)
    
    print("Memuat model GloVe...")
    glove_model = GloVeModel()
    glove_vectors_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/vectors/glove_verses.pkl')
    glove_model.load_model()
    glove_model.load_verse_vectors(glove_vectors_path)
    
    return word2vec_model, fasttext_model, glove_model

def generate_evaluation_form(word2vec_model, fasttext_model, glove_model, queries, top_k=5):
    """
    Menghasilkan formulir evaluasi untuk ditinjau oleh pakar
    
    Args:
        word2vec_model: Model Word2Vec
        fasttext_model: Model FastText
        glove_model: Model GloVe
        queries: Daftar query untuk evaluasi
        top_k: Jumlah hasil teratas yang akan ditampilkan
    """
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/qualitative')
    os.makedirs(output_dir, exist_ok=True)
    
    evaluation_data = {}
    
    for query in queries:
        print(f"\nMemproses query: '{query}'")
        
        # Cari menggunakan ketiga model
        word2vec_results = word2vec_model.search(query, limit=top_k)
        fasttext_results = fasttext_model.search(query, limit=top_k)
        glove_results = glove_model.search(query, limit=top_k)
        
        # Kumpulkan hasil
        query_results = {
            'word2vec': [
                {
                    'verse_id': f"{r['surah_number']}:{r['ayat_number']}",
                    'surah_name': r['surah_name'],
                    'arabic': r['arabic'],
                    'translation': r['translation'],
                    'similarity': r['similarity']
                }
                for r in word2vec_results
            ],
            'fasttext': [
                {
                    'verse_id': f"{r['surah_number']}:{r['ayat_number']}",
                    'surah_name': r['surah_name'],
                    'arabic': r['arabic'],
                    'translation': r['translation'],
                    'similarity': r['similarity']
                }
                for r in fasttext_results
            ],
            'glove': [
                {
                    'verse_id': f"{r['surah_number']}:{r['ayat_number']}",
                    'surah_name': r['surah_name'],
                    'arabic': r['arabic'],
                    'translation': r['translation'],
                    'similarity': r['similarity']
                }
                for r in glove_results
            ]
        }
        
        evaluation_data[query] = query_results
    
    # Simpan hasil ke file JSON untuk referensi
    with open(os.path.join(output_dir, 'evaluation_data.json'), 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
    
    # Buat formulir evaluasi HTML
    create_html_evaluation_form(evaluation_data, os.path.join(output_dir, 'evaluation_form.html'))
    
    # Buat formulir evaluasi Excel
    create_excel_evaluation_form(evaluation_data, os.path.join(output_dir, 'evaluation_form.xlsx'))
    
    print(f"\nFormulir evaluasi disimpan di direktori '{output_dir}'")
    print("Silakan minta pakar untuk mengisi formulir evaluasi dan menilai relevansi hasil.")

def create_html_evaluation_form(evaluation_data, output_file):
    """
    Membuat formulir evaluasi dalam format HTML
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Formulir Evaluasi Kualitatif Model Pencarian Semantik Al-Quran</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            h1 { color: #2c3e50; text-align: center; }
            h2 { color: #3498db; margin-top: 30px; }
            h3 { color: #2980b9; }
            .instructions { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .query { background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .arabic { font-family: "Traditional Arabic", "Scheherazade New", serif; font-size: 1.2rem; text-align: right; direction: rtl; }
            .relevance { width: 120px; }
            .model-header { background-color: #3498db; color: white; }
            .footer { margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>Formulir Evaluasi Kualitatif Model Pencarian Semantik Al-Quran</h1>
        
        <div class="instructions">
            <h3>Petunjuk Pengisian:</h3>
            <ol>
                <li>Formulir ini bertujuan untuk mengevaluasi relevansi hasil pencarian dari tiga model yang berbeda.</li>
                <li>Untuk setiap query pencarian, terdapat hasil dari model Word2Vec, FastText, dan GloVe.</li>
                <li>Mohon berikan penilaian relevansi untuk setiap ayat dengan skala berikut:
                    <ul>
                        <li><strong>0</strong> - Tidak relevan sama sekali</li>
                        <li><strong>1</strong> - Sedikit relevan</li>
                        <li><strong>2</strong> - Cukup relevan</li>
                        <li><strong>3</strong> - Sangat relevan</li>
                    </ul>
                </li>
                <li>Jika memungkinkan, berikan komentar singkat mengenai kualitas hasil dari masing-masing model.</li>
            </ol>
        </div>
    """
    
    for i, (query, results) in enumerate(evaluation_data.items()):
        html_content += f"""
        <h2>Query {i+1}: "{query}"</h2>
        
        <h3>Hasil Model Word2Vec</h3>
        <table>
            <tr>
                <th>No</th>
                <th>Ayat</th>
                <th>Teks Arab</th>
                <th>Terjemahan</th>
                <th>Skor Kesamaan</th>
                <th class="relevance">Relevansi (0-3)</th>
            </tr>
        """
        
        for j, result in enumerate(results['word2vec']):
            html_content += f"""
            <tr>
                <td>{j+1}</td>
                <td>{result['surah_name']} ({result['verse_id']})</td>
                <td class="arabic">{result['arabic']}</td>
                <td>{result['translation']}</td>
                <td>{result['similarity']:.4f}</td>
                <td class="relevance">
                    <select name="w2v_{i}_{j}">
                        <option value="0">0 - Tidak relevan</option>
                        <option value="1">1 - Sedikit relevan</option>
                        <option value="2">2 - Cukup relevan</option>
                        <option value="3">3 - Sangat relevan</option>
                    </select>
                </td>
            </tr>
            """
        
        html_content += """
        </table>
        <p><strong>Komentar untuk hasil Word2Vec:</strong></p>
        <textarea rows="3" style="width: 100%;"></textarea>
        
        """
        
        html_content += f"""
        <h3>Hasil Model FastText</h3>
        <table>
            <tr>
                <th>No</th>
                <th>Ayat</th>
                <th>Teks Arab</th>
                <th>Terjemahan</th>
                <th>Skor Kesamaan</th>
                <th class="relevance">Relevansi (0-3)</th>
            </tr>
        """
        
        for j, result in enumerate(results['fasttext']):
            html_content += f"""
            <tr>
                <td>{j+1}</td>
                <td>{result['surah_name']} ({result['verse_id']})</td>
                <td class="arabic">{result['arabic']}</td>
                <td>{result['translation']}</td>
                <td>{result['similarity']:.4f}</td>
                <td class="relevance">
                    <select name="ft_{i}_{j}">
                        <option value="0">0 - Tidak relevan</option>
                        <option value="1">1 - Sedikit relevan</option>
                        <option value="2">2 - Cukup relevan</option>
                        <option value="3">3 - Sangat relevan</option>
                    </select>
                </td>
            </tr>
            """
        
        html_content += """
        </table>
        <p><strong>Komentar untuk hasil FastText:</strong></p>
        <textarea rows="3" style="width: 100%;"></textarea>
        
        """
        
        html_content += f"""
        <h3>Hasil Model GloVe</h3>
        <table>
            <tr>
                <th>No</th>
                <th>Ayat</th>
                <th>Teks Arab</th>
                <th>Terjemahan</th>
                <th>Skor Kesamaan</th>
                <th class="relevance">Relevansi (0-3)</th>
            </tr>
        """
        
        for j, result in enumerate(results['glove']):
            html_content += f"""
            <tr>
                <td>{j+1}</td>
                <td>{result['surah_name']} ({result['verse_id']})</td>
                <td class="arabic">{result['arabic']}</td>
                <td>{result['translation']}</td>
                <td>{result['similarity']:.4f}</td>
                <td class="relevance">
                    <select name="glove_{i}_{j}">
                        <option value="0">0 - Tidak relevan</option>
                        <option value="1">1 - Sedikit relevan</option>
                        <option value="2">2 - Cukup relevan</option>
                        <option value="3">3 - Sangat relevan</option>
                    </select>
                </td>
            </tr>
            """
        
        html_content += """
        </table>
        <p><strong>Komentar untuk hasil GloVe:</strong></p>
        <textarea rows="3" style="width: 100%;"></textarea>
        
        <hr>
        """
    
    html_content += """
        <div class="footer">
            <p><strong>Evaluasi Keseluruhan:</strong></p>
            <p>Dari ketiga model di atas, model mana yang menurut Anda memberikan hasil paling relevan?</p>
            <select name="best_model">
                <option value="word2vec">Word2Vec</option>
                <option value="fasttext">FastText</option>
                <option value="glove">GloVe</option>
            </select>
            
            <p>Mohon berikan komentar umum mengenai perbandingan ketiga model:</p>
            <textarea rows="5" style="width: 100%;"></textarea>
            
            <p><strong>Nama Evaluator:</strong> ___________________________</p>
            <p><strong>Keahlian:</strong> ___________________________</p>
            <p><strong>Tanggal:</strong> ___________________________</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_excel_evaluation_form(evaluation_data, output_file):
    """
    Membuat formulir evaluasi dalam format Excel
    """
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    workbook = writer.book
    
    # Format untuk header
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#3498db',
        'color': 'white',
        'border': 1
    })
    
    # Format untuk sel biasa
    cell_format = workbook.add_format({
        'border': 1
    })
    
    # Format untuk skor kesamaan
    score_format = workbook.add_format({
        'border': 1,
        'num_format': '0.0000'
    })
    
    # Buat sheet petunjuk
    instructions = workbook.add_worksheet('Petunjuk')
    instructions.set_column('A:A', 80)
    
    instructions.write('A1', 'PETUNJUK PENGISIAN FORMULIR EVALUASI', header_format)
    instructions.write('A2', '1. Formulir ini bertujuan untuk mengevaluasi relevansi hasil pencarian dari tiga model yang berbeda.', cell_format)
    instructions.write('A3', '2. Untuk setiap query pencarian, terdapat hasil dari model Word2Vec, FastText, dan GloVe.', cell_format)
    instructions.write('A4', '3. Mohon berikan penilaian relevansi untuk setiap ayat dengan skala berikut:', cell_format)
    instructions.write('A5', '   - 0: Tidak relevan sama sekali', cell_format)
    instructions.write('A6', '   - 1: Sedikit relevan', cell_format)
    instructions.write('A7', '   - 2: Cukup relevan', cell_format)
    instructions.write('A8', '   - 3: Sangat relevan', cell_format)
    instructions.write('A9', '4. Mohon isi kolom "Relevansi (0-3)" untuk setiap hasil.', cell_format)
    instructions.write('A10', '5. Jika memungkinkan, berikan komentar singkat mengenai kualitas hasil dari masing-masing model.', cell_format)
    instructions.write('A11', '6. Pada sheet "Evaluasi Keseluruhan", berikan evaluasi umum mengenai perbandingan ketiga model.', cell_format)
    
    # Buat sheet untuk setiap query
    for i, (query, results) in enumerate(evaluation_data.items()):
        sheet_name = f"Query {i+1}"
        worksheet = workbook.add_worksheet(sheet_name)
        
        # Atur lebar kolom
        worksheet.set_column('A:A', 5)   # No
        worksheet.set_column('B:B', 20)  # Ayat
        worksheet.set_column('C:C', 30)  # Teks Arab
        worksheet.set_column('D:D', 40)  # Terjemahan
        worksheet.set_column('E:E', 15)  # Skor Kesamaan
        worksheet.set_column('F:F', 15)  # Relevansi
        worksheet.set_column('G:G', 30)  # Komentar
        
        # Tulis query
        worksheet.merge_range('A1:G1', f'Query: "{query}"', header_format)
        
        # Hasil Word2Vec
        row = 2
        worksheet.merge_range(f'A{row}:G{row}', 'Hasil Model Word2Vec', header_format)
        row += 1
        
        # Header kolom
        worksheet.write(f'A{row}', 'No', header_format)
        worksheet.write(f'B{row}', 'Ayat', header_format)
        worksheet.write(f'C{row}', 'Teks Arab', header_format)
        worksheet.write(f'D{row}', 'Terjemahan', header_format)
        worksheet.write(f'E{row}', 'Skor Kesamaan', header_format)
        worksheet.write(f'F{row}', 'Relevansi (0-3)', header_format)
        worksheet.write(f'G{row}', 'Komentar', header_format)
        row += 1
        
        # Hasil Word2Vec
        for j, result in enumerate(results['word2vec']):
            worksheet.write(f'A{row}', j+1, cell_format)
            worksheet.write(f'B{row}', f"{result['surah_name']} ({result['verse_id']})", cell_format)
            worksheet.write(f'C{row}', result['arabic'], cell_format)
            worksheet.write(f'D{row}', result['translation'], cell_format)
            worksheet.write(f'E{row}', result['similarity'], score_format)
            worksheet.write(f'F{row}', '', cell_format)
            worksheet.write(f'G{row}', '', cell_format)
            row += 1
        
        # Spasi
        row += 1
        
        # Hasil FastText
        worksheet.merge_range(f'A{row}:G{row}', 'Hasil Model FastText', header_format)
        row += 1
        
        # Header kolom
        worksheet.write(f'A{row}', 'No', header_format)
        worksheet.write(f'B{row}', 'Ayat', header_format)
        worksheet.write(f'C{row}', 'Teks Arab', header_format)
        worksheet.write(f'D{row}', 'Terjemahan', header_format)
        worksheet.write(f'E{row}', 'Skor Kesamaan', header_format)
        worksheet.write(f'F{row}', 'Relevansi (0-3)', header_format)
        worksheet.write(f'G{row}', 'Komentar', header_format)
        row += 1
        
        # Hasil FastText
        for j, result in enumerate(results['fasttext']):
            worksheet.write(f'A{row}', j+1, cell_format)
            worksheet.write(f'B{row}', f"{result['surah_name']} ({result['verse_id']})", cell_format)
            worksheet.write(f'C{row}', result['arabic'], cell_format)
            worksheet.write(f'D{row}', result['translation'], cell_format)
            worksheet.write(f'E{row}', result['similarity'], score_format)
            worksheet.write(f'F{row}', '', cell_format)
            worksheet.write(f'G{row}', '', cell_format)
            row += 1
        
        # Spasi
        row += 1
        
        # Hasil GloVe
        worksheet.merge_range(f'A{row}:G{row}', 'Hasil Model GloVe', header_format)
        row += 1
        
        # Header kolom
        worksheet.write(f'A{row}', 'No', header_format)
        worksheet.write(f'B{row}', 'Ayat', header_format)
        worksheet.write(f'C{row}', 'Teks Arab', header_format)
        worksheet.write(f'D{row}', 'Terjemahan', header_format)
        worksheet.write(f'E{row}', 'Skor Kesamaan', header_format)
        worksheet.write(f'F{row}', 'Relevansi (0-3)', header_format)
        worksheet.write(f'G{row}', 'Komentar', header_format)
        row += 1
        
        # Hasil GloVe
        for j, result in enumerate(results['glove']):
            worksheet.write(f'A{row}', j+1, cell_format)
            worksheet.write(f'B{row}', f"{result['surah_name']} ({result['verse_id']})", cell_format)
            worksheet.write(f'C{row}', result['arabic'], cell_format)
            worksheet.write(f'D{row}', result['translation'], cell_format)
            worksheet.write(f'E{row}', result['similarity'], score_format)
            worksheet.write(f'F{row}', '', cell_format)
            worksheet.write(f'G{row}', '', cell_format)
            row += 1
    
    # Buat sheet evaluasi keseluruhan
    overall = workbook.add_worksheet('Evaluasi Keseluruhan')
    overall.set_column('A:A', 30)
    overall.set_column('B:B', 50)
    
    overall.write('A1', 'EVALUASI KESELURUHAN', header_format)
    overall.write('A2', 'Model terbaik menurut Anda:', cell_format)
    overall.write('B2', '', cell_format)
    overall.write('A3', 'Komentar umum:', cell_format)
    overall.write('B3', '', cell_format)
    overall.write('A4', 'Nama Evaluator:', cell_format)
    overall.write('B4', '', cell_format)
    overall.write('A5', 'Keahlian:', cell_format)
    overall.write('B5', '', cell_format)
    overall.write('A6', 'Tanggal:', cell_format)
    overall.write('B6', '', cell_format)
    
    writer.close()

def analyze_expert_feedback(feedback_file):
    """
    Menganalisis hasil evaluasi pakar
    
    Args:
        feedback_file: Path ke file hasil evaluasi (JSON format)
    """
    with open(feedback_file, 'r', encoding='utf-8') as f:
        feedback = json.load(f)
    
    # Hitung rata-rata skor relevansi untuk setiap model
    models = ['word2vec', 'fasttext', 'glove']
    
    relevance_scores = {model: [] for model in models}
    expert_preferences = {model: 0 for model in models}
    
    # Kumpulkan skor relevansi
    for query_results in feedback['query_results']:
        for model in models:
            model_scores = query_results[model]['relevance_scores']
            relevance_scores[model].extend(model_scores)
    
    # Hitung jumlah preferensi pakar
    for expert_feedback in feedback['expert_feedback']:
        best_model = expert_feedback['best_model']
        if best_model in expert_preferences:
            expert_preferences[best_model] += 1
    
    # Hitung rata-rata skor relevansi
    avg_relevance = {model: sum(scores)/len(scores) if scores else 0 for model, scores in relevance_scores.items()}
    
    # Tampilkan hasil
    print("\n=== HASIL ANALISIS EVALUASI KUALITATIF ===")
    
    # Tabel skor relevansi
    relevance_table = [
        ["Model", "Skor Relevansi Rata-rata", "Jumlah Preferensi Pakar"]
    ]
    
    for model in models:
        relevance_table.append([
            model.capitalize(),
            f"{avg_relevance[model]:.2f}",
            f"{expert_preferences[model]}"
        ])
    
    print(tabulate(relevance_table, headers="firstrow", tablefmt="grid"))
    
    # Buat visualisasi
    plt.figure(figsize=(12, 5))
    
    # Plot skor relevansi
    plt.subplot(1, 2, 1)
    plt.bar(models, [avg_relevance[model] for model in models])
    plt.title('Skor Relevansi Rata-rata')
    plt.xlabel('Model')
    plt.ylabel('Skor (0-3)')
    
    # Plot preferensi pakar
    plt.subplot(1, 2, 2)
    plt.bar(models, [expert_preferences[model] for model in models])
    plt.title('Preferensi Pakar')
    plt.xlabel('Model')
    plt.ylabel('Jumlah Preferensi')
    
    plt.tight_layout()
    
    # Simpan grafik
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/qualitative')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'expert_evaluation_analysis.png'))
    
    print(f"\nGrafik analisis disimpan di '{os.path.join(output_dir, 'expert_evaluation_analysis.png')}'")
    
    # Kumpulkan komentar
    print("\n=== KOMENTAR PAKAR ===")
    for i, expert in enumerate(feedback['expert_feedback']):
        print(f"\nPakar {i+1} ({expert['name']}, {expert['expertise']}):")
        print(f"Model pilihan: {expert['best_model'].capitalize()}")
        print(f"Komentar umum: {expert['comment']}")

def main():
    """
    Fungsi utama
    """
    print("=== EVALUASI KUALITATIF MODEL PENCARIAN SEMANTIK AL-QURAN ===")
    
    try:
        # Contoh query untuk evaluasi
        evaluation_queries = [
            "berdoa kepada Allah",
            "jalan yang lurus",
            "berbakti kepada orang tua",
            "larangan riba",
            "sikap sabar menghadapi cobaan",
            "keutamaan sedekah",
            "memaafkan kesalahan orang lain",
            "larangan sombong",
            "keesaan Allah"
        ]
        
        # Tentukan mode operasi
        mode = input("Pilih mode operasi:\n1. Buat formulir evaluasi untuk pakar\n2. Analisis hasil evaluasi pakar\nPilihan (1/2): ")
        
        if mode == "1":
            # Muat model
            word2vec_model, fasttext_model, glove_model = load_models()
            
            # Buat formulir evaluasi
            generate_evaluation_form(word2vec_model, fasttext_model, glove_model, evaluation_queries)
            
        elif mode == "2":
            # Path ke file hasil evaluasi
            feedback_file = input("Masukkan path ke file hasil evaluasi (JSON): ")
            
            # Analisis hasil evaluasi
            analyze_expert_feedback(feedback_file)
            
        else:
            print("Pilihan tidak valid.")
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 