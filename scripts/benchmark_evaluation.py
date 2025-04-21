"""
Script untuk evaluasi mendalam dari model Word2Vec, FastText, dan GloVe
menggunakan benchmark dataset dan metrik evaluasi
"""
import os
import sys
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from sklearn.metrics import precision_score, recall_score, f1_score

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

def create_benchmark_dataset():
    """
    Membuat atau memuat benchmark dataset untuk evaluasi
    
    Dataset terdiri dari query dan daftar ayat yang relevan
    """
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/benchmark/evaluation_dataset.json')
    
    # Jika dataset sudah ada, muat dari file
    if os.path.exists(dataset_path):
        print(f"Memuat benchmark dataset dari {dataset_path}")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            benchmark_data = json.load(f)
        return benchmark_data
    
    # Jika tidak, buat dataset baru
    print("Membuat benchmark dataset baru...")
    
    # Contoh dataset: query dan daftar ayat yang relevan (format: surah_number:ayat_number)
    benchmark_data = [
        {
            "query": "berdoa kepada Allah",
            "relevant_verses": ["2:186", "7:55", "40:60", "2:201", "3:38", "3:147", "7:180", "7:189", "10:12", "10:22", "17:11"]
        },
        {
            "query": "jalan yang lurus",
            "relevant_verses": ["1:6", "1:7", "2:142", "2:213", "3:51", "4:68", "5:16", "6:39", "6:87", "6:161", "7:16"]
        },
        {
            "query": "berbakti kepada orang tua",
            "relevant_verses": ["2:83", "4:36", "6:151", "17:23", "17:24", "19:14", "29:8", "31:14", "46:15", "46:17", "31:15"]
        },
        {
            "query": "larangan riba",
            "relevant_verses": ["2:275", "2:276", "2:278", "2:279", "3:130", "4:161", "30:39"]
        },
        {
            "query": "sikap sabar menghadapi cobaan",
            "relevant_verses": ["2:45", "2:153", "2:155", "2:177", "2:249", "3:120", "3:142", "3:146", "3:186", "3:200", "7:126", "11:115", "13:22", "16:42", "16:126", "29:58", "39:10", "41:35", "70:5"]
        },
        {
            "query": "keutamaan sedekah",
            "relevant_verses": ["2:195", "2:261", "2:262", "2:264", "2:265", "2:267", "2:270", "2:271", "2:273", "2:274", "3:92", "3:134", "4:114", "9:99", "9:103", "9:104", "57:18", "63:10", "64:16"]
        },
        {
            "query": "hari kiamat",
            "relevant_verses": ["1:4", "2:85", "2:113", "2:174", "3:77", "3:180", "3:185", "3:194", "4:87", "4:109", "4:141", "4:159", "5:36", "6:12", "7:32", "7:167", "10:60", "10:93", "11:98", "11:99", "11:103", "11:104", "11:105", "16:25", "16:27", "16:92", "16:124", "17:13", "17:14", "17:58", "17:97", "18:105", "19:95", "20:100", "20:101", "20:102", "20:124", "21:47", "21:49", "22:1", "22:2", "22:7", "22:9", "22:17", "22:69", "23:16", "25:11", "25:14", "25:69", "26:82", "28:41", "28:42", "28:61", "28:71", "28:72", "28:74", "29:13", "29:25", "31:34", "32:25", "35:14", "39:15", "39:24", "39:31", "39:47", "39:60", "39:67", "41:40", "42:7", "42:45", "45:17", "45:26", "46:5", "58:7", "60:3", "68:39", "75:1", "75:6", "81:1-14", "82:1-5", "99:1-8", "100:9-11", "101:1-11"]
        },
        {
            "query": "memaafkan kesalahan orang lain",
            "relevant_verses": ["2:109", "3:134", "3:159", "4:149", "5:13", "7:199", "15:85", "24:22", "41:34", "42:37", "42:40", "42:43", "64:14"]
        },
        {
            "query": "larangan sombong",
            "relevant_verses": ["4:36", "7:146", "16:23", "17:37", "31:18", "31:19", "57:23", "16:29", "39:60", "39:72", "40:76"]
        },
        {
            "query": "keesaan Allah",
            "relevant_verses": ["2:163", "2:255", "3:2", "3:18", "4:87", "4:171", "5:73", "6:19", "9:31", "12:39", "13:16", "14:52", "16:22", "16:51", "17:42", "17:111", "18:110", "20:8", "20:14", "20:98", "21:25", "21:87", "21:108", "22:34", "23:91", "23:116", "27:26", "28:70", "28:88", "35:3", "37:35", "38:65", "39:4", "40:3", "40:62", "40:65", "41:6", "44:8", "47:19", "59:22", "59:23", "112:1-4"]
        }
    ]
    
    # Pastikan direktori ada
    os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
    
    # Simpan dataset
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
    
    print(f"Benchmark dataset disimpan di {dataset_path}")
    return benchmark_data

def evaluate_models(word2vec_model, fasttext_model, glove_model, benchmark_data, threshold=0.5, top_k=10):
    """
    Evaluasi model menggunakan benchmark dataset dan metrik evaluasi
    
    Args:
        word2vec_model: Model Word2Vec
        fasttext_model: Model FastText
        glove_model: Model GloVe
        benchmark_data: Dataset benchmark untuk evaluasi
        threshold: Threshold untuk kesamaan kosinus
        top_k: Jumlah hasil teratas yang dipertimbangkan
    
    Returns:
        Dict dengan hasil evaluasi
    """
    print("\nEvaluasi model dengan benchmark dataset...")
    
    results = {
        'word2vec': {
            'precision': [],
            'recall': [],
            'f1_score': [],
            'execution_time': []
        },
        'fasttext': {
            'precision': [],
            'recall': [],
            'f1_score': [],
            'execution_time': []
        },
        'glove': {
            'precision': [],
            'recall': [],
            'f1_score': [],
            'execution_time': []
        }
    }
    
    for i, data in enumerate(benchmark_data):
        query = data['query']
        relevant_verses = set(data['relevant_verses'])
        
        print(f"\nQuery {i+1}: '{query}'")
        print(f"Jumlah ayat relevan: {len(relevant_verses)}")
        
        # Evaluasi Word2Vec
        start_time = time.time()
        word2vec_search_results = word2vec_model.search(query, threshold=threshold, limit=100)
        word2vec_time = time.time() - start_time
        results['word2vec']['execution_time'].append(word2vec_time)
        
        # Ekstrak ID ayat dari hasil
        word2vec_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in word2vec_search_results[:top_k]]
        word2vec_relevant_retrieved = set(word2vec_retrieved) & relevant_verses
        
        # Hitung metrik
        word2vec_precision = len(word2vec_relevant_retrieved) / len(word2vec_retrieved) if word2vec_retrieved else 0
        word2vec_recall = len(word2vec_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
        word2vec_f1 = 2 * (word2vec_precision * word2vec_recall) / (word2vec_precision + word2vec_recall) if (word2vec_precision + word2vec_recall) > 0 else 0
        
        results['word2vec']['precision'].append(word2vec_precision)
        results['word2vec']['recall'].append(word2vec_recall)
        results['word2vec']['f1_score'].append(word2vec_f1)
        
        print(f"Word2Vec - Precision: {word2vec_precision:.4f}, Recall: {word2vec_recall:.4f}, F1: {word2vec_f1:.4f}, Time: {word2vec_time:.4f}s")
        
        # Evaluasi FastText
        start_time = time.time()
        fasttext_search_results = fasttext_model.search(query, threshold=threshold, limit=100)
        fasttext_time = time.time() - start_time
        results['fasttext']['execution_time'].append(fasttext_time)
        
        # Ekstrak ID ayat dari hasil
        fasttext_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in fasttext_search_results[:top_k]]
        fasttext_relevant_retrieved = set(fasttext_retrieved) & relevant_verses
        
        # Hitung metrik
        fasttext_precision = len(fasttext_relevant_retrieved) / len(fasttext_retrieved) if fasttext_retrieved else 0
        fasttext_recall = len(fasttext_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
        fasttext_f1 = 2 * (fasttext_precision * fasttext_recall) / (fasttext_precision + fasttext_recall) if (fasttext_precision + fasttext_recall) > 0 else 0
        
        results['fasttext']['precision'].append(fasttext_precision)
        results['fasttext']['recall'].append(fasttext_recall)
        results['fasttext']['f1_score'].append(fasttext_f1)
        
        print(f"FastText - Precision: {fasttext_precision:.4f}, Recall: {fasttext_recall:.4f}, F1: {fasttext_f1:.4f}, Time: {fasttext_time:.4f}s")
        
        # Evaluasi GloVe
        start_time = time.time()
        glove_search_results = glove_model.search(query, threshold=threshold, limit=100)
        glove_time = time.time() - start_time
        results['glove']['execution_time'].append(glove_time)
        
        # Ekstrak ID ayat dari hasil
        glove_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in glove_search_results[:top_k]]
        glove_relevant_retrieved = set(glove_retrieved) & relevant_verses
        
        # Hitung metrik
        glove_precision = len(glove_relevant_retrieved) / len(glove_retrieved) if glove_retrieved else 0
        glove_recall = len(glove_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
        glove_f1 = 2 * (glove_precision * glove_recall) / (glove_precision + glove_recall) if (glove_precision + glove_recall) > 0 else 0
        
        results['glove']['precision'].append(glove_precision)
        results['glove']['recall'].append(glove_recall)
        results['glove']['f1_score'].append(glove_f1)
        
        print(f"GloVe - Precision: {glove_precision:.4f}, Recall: {glove_recall:.4f}, F1: {glove_f1:.4f}, Time: {glove_time:.4f}s")
    
    return results

def print_evaluation_results(results, benchmark_data):
    """
    Menampilkan hasil evaluasi dalam bentuk tabel
    """
    # Siapkan data tabel untuk perbandingan metrik
    table_data = []
    
    # Hitung rata-rata metrik
    avg_precision_w2v = np.mean(results['word2vec']['precision'])
    avg_recall_w2v = np.mean(results['word2vec']['recall'])
    avg_f1_w2v = np.mean(results['word2vec']['f1_score'])
    avg_time_w2v = np.mean(results['word2vec']['execution_time'])
    
    avg_precision_ft = np.mean(results['fasttext']['precision'])
    avg_recall_ft = np.mean(results['fasttext']['recall'])
    avg_f1_ft = np.mean(results['fasttext']['f1_score'])
    avg_time_ft = np.mean(results['fasttext']['execution_time'])
    
    avg_precision_glove = np.mean(results['glove']['precision'])
    avg_recall_glove = np.mean(results['glove']['recall'])
    avg_f1_glove = np.mean(results['glove']['f1_score'])
    avg_time_glove = np.mean(results['glove']['execution_time'])
    
    # Tampilkan hasil untuk setiap query
    for i, data in enumerate(benchmark_data):
        row = [
            i+1,
            data['query'][:30] + "..." if len(data['query']) > 30 else data['query'],
            f"{results['word2vec']['precision'][i]:.4f}",
            f"{results['fasttext']['precision'][i]:.4f}",
            f"{results['glove']['precision'][i]:.4f}",
            f"{results['word2vec']['recall'][i]:.4f}",
            f"{results['fasttext']['recall'][i]:.4f}",
            f"{results['glove']['recall'][i]:.4f}",
            f"{results['word2vec']['f1_score'][i]:.4f}",
            f"{results['fasttext']['f1_score'][i]:.4f}",
            f"{results['glove']['f1_score'][i]:.4f}"
        ]
        table_data.append(row)
    
    # Tambahkan baris rata-rata
    avg_row = [
        "",
        "RATA-RATA",
        f"{avg_precision_w2v:.4f}",
        f"{avg_precision_ft:.4f}",
        f"{avg_precision_glove:.4f}",
        f"{avg_recall_w2v:.4f}",
        f"{avg_recall_ft:.4f}",
        f"{avg_recall_glove:.4f}",
        f"{avg_f1_w2v:.4f}",
        f"{avg_f1_ft:.4f}",
        f"{avg_f1_glove:.4f}"
    ]
    table_data.append(avg_row)
    
    # Header tabel
    headers = [
        "No", 
        "Query", 
        "P (W2V)", 
        "P (FT)", 
        "P (GloVe)",
        "R (W2V)", 
        "R (FT)", 
        "R (GloVe)",
        "F1 (W2V)", 
        "F1 (FT)", 
        "F1 (GloVe)"
    ]
    
    print("\n=== HASIL EVALUASI MENGGUNAKAN BENCHMARK DATASET ===")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Tampilkan rata-rata eksekusi waktu
    print("\nRata-rata Waktu Eksekusi:")
    print(f"Word2Vec: {avg_time_w2v:.4f} detik")
    print(f"FastText: {avg_time_ft:.4f} detik")
    print(f"GloVe: {avg_time_glove:.4f} detik")
    
    # Simpan hasil evaluasi ke file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    evaluation_results = {
        'word2vec': {
            'precision': float(avg_precision_w2v),
            'recall': float(avg_recall_w2v),
            'f1_score': float(avg_f1_w2v),
            'execution_time': float(avg_time_w2v)
        },
        'fasttext': {
            'precision': float(avg_precision_ft),
            'recall': float(avg_recall_ft),
            'f1_score': float(avg_f1_ft),
            'execution_time': float(avg_time_ft)
        },
        'glove': {
            'precision': float(avg_precision_glove),
            'recall': float(avg_recall_glove),
            'f1_score': float(avg_f1_glove),
            'execution_time': float(avg_time_glove)
        }
    }
    
    with open(os.path.join(output_dir, 'evaluation_results.json'), 'w') as f:
        json.dump(evaluation_results, f, indent=2)

def plot_evaluation_results(results):
    """
    Membuat visualisasi hasil evaluasi
    """
    # Siapkan data
    models = ['Word2Vec', 'FastText', 'GloVe']
    
    precision = [
        np.mean(results['word2vec']['precision']),
        np.mean(results['fasttext']['precision']),
        np.mean(results['glove']['precision'])
    ]
    
    recall = [
        np.mean(results['word2vec']['recall']),
        np.mean(results['fasttext']['recall']),
        np.mean(results['glove']['recall'])
    ]
    
    f1_score = [
        np.mean(results['word2vec']['f1_score']),
        np.mean(results['fasttext']['f1_score']),
        np.mean(results['glove']['f1_score'])
    ]
    
    execution_time = [
        np.mean(results['word2vec']['execution_time']),
        np.mean(results['fasttext']['execution_time']),
        np.mean(results['glove']['execution_time'])
    ]
    
    # Buat direktori untuk hasil
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot metrik evaluasi
    x = np.arange(len(models))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    rects1 = ax.bar(x - width, precision, width, label='Precision')
    rects2 = ax.bar(x, recall, width, label='Recall')
    rects3 = ax.bar(x + width, f1_score, width, label='F1-Score')
    
    ax.set_title('Perbandingan Metrik Evaluasi')
    ax.set_ylabel('Nilai')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    
    # Tambahkan label nilai
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{:.3f}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)
    
    # Simpan grafik
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'evaluation_metrics.png'))
    
    # Plot waktu eksekusi
    fig, ax = plt.subplots(figsize=(10, 5))
    
    bars = ax.bar(models, execution_time, color='green')
    
    ax.set_title('Perbandingan Waktu Eksekusi')
    ax.set_ylabel('Waktu (detik)')
    ax.set_xlabel('Model')
    
    # Tambahkan label nilai
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{:.4f}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # Simpan grafik
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'execution_time.png'))
    
    print(f"\nGrafik evaluasi disimpan di direktori '{output_dir}'")

def main():
    """
    Fungsi utama
    """
    print("=== EVALUASI MODEL WORD2VEC, FASTTEXT, DAN GLOVE ===")
    
    try:
        # Buat atau muat benchmark dataset
        benchmark_data = create_benchmark_dataset()
        
        # Muat model
        word2vec_model, fasttext_model, glove_model = load_models()
        
        # Evaluasi model
        evaluation_results = evaluate_models(word2vec_model, fasttext_model, glove_model, benchmark_data)
        
        # Tampilkan hasil evaluasi
        print_evaluation_results(evaluation_results, benchmark_data)
        
        # Buat visualisasi hasil evaluasi
        plot_evaluation_results(evaluation_results)
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 