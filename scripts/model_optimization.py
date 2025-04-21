"""
Script untuk fine-tuning parameter model dan mengoptimalkan algoritma embedding ayat
"""
import os
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
from collections import defaultdict

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel
from backend.preprocessing import process_quran_data

def load_models():
    """
    Memuat model Word2Vec dan FastText
    """
    print("Memuat model Word2Vec...")
    word2vec_model = Word2VecModel()
    word2vec_model.load_model()
    
    print("Memuat model FastText...")
    fasttext_model = FastTextModel()
    fasttext_model.load_model()
    
    return word2vec_model, fasttext_model

def load_benchmark_dataset():
    """
    Memuat benchmark dataset untuk evaluasi
    """
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/benchmark/evaluation_dataset.json')
    
    if not os.path.exists(dataset_path):
        print(f"Error: Benchmark dataset tidak ditemukan di {dataset_path}")
        print("Jalankan scripts/benchmark_evaluation.py terlebih dahulu untuk membuat dataset.")
        sys.exit(1)
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)
    
    print(f"Memuat {len(benchmark_data)} query dari benchmark dataset")
    return benchmark_data

def experiment_embedding_algorithms(word2vec_model, fasttext_model, preprocessed_verses, queries, relevant_verses_dict):
    """
    Eksperimen dengan berbagai algoritma embedding ayat
    
    Args:
        word2vec_model: Model Word2Vec
        fasttext_model: Model FastText
        preprocessed_verses: Data ayat yang telah diproses
        queries: Daftar query untuk evaluasi
        relevant_verses_dict: Dict dengan query sebagai kunci dan daftar ayat relevan sebagai nilai
    
    Returns:
        Dict dengan hasil eksperimen
    """
    print("\n=== EKSPERIMEN ALGORITMA EMBEDDING AYAT ===")
    
    # Algoritma embedding yang akan diuji
    embedding_algorithms = {
        'mean': lambda vectors: np.mean(vectors, axis=0) if vectors else None,
        'weighted_mean': lambda vectors: np.average(vectors, axis=0, weights=np.linspace(1.0, 0.5, len(vectors))) if vectors else None,
        'max_pooling': lambda vectors: np.max(vectors, axis=0) if vectors else None,
        'min_max_pooling': lambda vectors: np.concatenate((np.min(vectors, axis=0), np.max(vectors, axis=0))) if vectors else None
    }
    
    results = {
        'word2vec': {algo: {'precision': [], 'recall': [], 'f1_score': [], 'execution_time': []} for algo in embedding_algorithms},
        'fasttext': {algo: {'precision': [], 'recall': [], 'f1_score': [], 'execution_time': []} for algo in embedding_algorithms}
    }
    
    # Untuk setiap algoritma embedding
    for algo_name, algo_func in embedding_algorithms.items():
        print(f"\nMenguji algoritma embedding: {algo_name}")
        
        # Word2Vec
        # Ganti fungsi kalkulasi vektor ayat
        original_w2v_calc_func = word2vec_model._calculate_verse_vector
        word2vec_model._calculate_verse_vector = lambda tokens: algo_func([word2vec_model.model[token] for token in tokens if token in word2vec_model.model])
        
        # Buat vektor ayat baru
        word2vec_model.create_verse_vectors(preprocessed_verses)
        
        # FastText
        # Ganti fungsi kalkulasi vektor ayat
        original_ft_calc_func = fasttext_model._calculate_verse_vector
        fasttext_model._calculate_verse_vector = lambda tokens: algo_func([fasttext_model.model[token] for token in tokens if token in fasttext_model.model])
        
        # Buat vektor ayat baru
        fasttext_model.create_verse_vectors(preprocessed_verses)
        
        # Evaluasi performa pada setiap query
        for query in queries:
            relevant_verses = set(relevant_verses_dict.get(query, []))
            
            if not relevant_verses:
                print(f"  Peringatan: Query '{query}' tidak memiliki ayat relevan yang ditentukan.")
                continue
            
            print(f"  Query: '{query}'")
            
            # Evaluasi Word2Vec
            start_time = time.time()
            word2vec_results = word2vec_model.search(query, limit=20)
            word2vec_time = time.time() - start_time
            
            # Ekstrak ID ayat dari hasil
            word2vec_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in word2vec_results]
            word2vec_relevant_retrieved = set(word2vec_retrieved) & relevant_verses
            
            # Hitung metrik
            word2vec_precision = len(word2vec_relevant_retrieved) / len(word2vec_retrieved) if word2vec_retrieved else 0
            word2vec_recall = len(word2vec_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
            word2vec_f1 = 2 * (word2vec_precision * word2vec_recall) / (word2vec_precision + word2vec_recall) if (word2vec_precision + word2vec_recall) > 0 else 0
            
            results['word2vec'][algo_name]['precision'].append(word2vec_precision)
            results['word2vec'][algo_name]['recall'].append(word2vec_recall)
            results['word2vec'][algo_name]['f1_score'].append(word2vec_f1)
            results['word2vec'][algo_name]['execution_time'].append(word2vec_time)
            
            # Evaluasi FastText
            start_time = time.time()
            fasttext_results = fasttext_model.search(query, limit=20)
            fasttext_time = time.time() - start_time
            
            # Ekstrak ID ayat dari hasil
            fasttext_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in fasttext_results]
            fasttext_relevant_retrieved = set(fasttext_retrieved) & relevant_verses
            
            # Hitung metrik
            fasttext_precision = len(fasttext_relevant_retrieved) / len(fasttext_retrieved) if fasttext_retrieved else 0
            fasttext_recall = len(fasttext_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
            fasttext_f1 = 2 * (fasttext_precision * fasttext_recall) / (fasttext_precision + fasttext_recall) if (fasttext_precision + fasttext_recall) > 0 else 0
            
            results['fasttext'][algo_name]['precision'].append(fasttext_precision)
            results['fasttext'][algo_name]['recall'].append(fasttext_recall)
            results['fasttext'][algo_name]['f1_score'].append(fasttext_f1)
            results['fasttext'][algo_name]['execution_time'].append(fasttext_time)
        
        # Kembalikan fungsi kalkulasi vektor asli
        word2vec_model._calculate_verse_vector = original_w2v_calc_func
        fasttext_model._calculate_verse_vector = original_ft_calc_func
    
    return results

def experiment_threshold_variation(word2vec_model, fasttext_model, queries, relevant_verses_dict):
    """
    Eksperimen dengan variasi threshold kesamaan kosinus
    
    Args:
        word2vec_model: Model Word2Vec
        fasttext_model: Model FastText
        queries: Daftar query untuk evaluasi
        relevant_verses_dict: Dict dengan query sebagai kunci dan daftar ayat relevan sebagai nilai
    
    Returns:
        Dict dengan hasil eksperimen
    """
    print("\n=== EKSPERIMEN THRESHOLD KESAMAAN KOSINUS ===")
    
    # Daftar threshold yang akan diuji
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    
    results = {
        'word2vec': {t: {'precision': [], 'recall': [], 'f1_score': [], 'result_count': []} for t in thresholds},
        'fasttext': {t: {'precision': [], 'recall': [], 'f1_score': [], 'result_count': []} for t in thresholds}
    }
    
    # Evaluasi performa pada setiap query
    for query in queries:
        relevant_verses = set(relevant_verses_dict.get(query, []))
        
        if not relevant_verses:
            print(f"  Peringatan: Query '{query}' tidak memiliki ayat relevan yang ditentukan.")
            continue
        
        print(f"  Query: '{query}'")
        
        # Uji setiap threshold
        for threshold in thresholds:
            print(f"    Threshold: {threshold}")
            
            # Word2Vec
            word2vec_results = word2vec_model.search(query, threshold=threshold, limit=100)
            
            # Ekstrak ID ayat dari hasil
            word2vec_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in word2vec_results]
            word2vec_relevant_retrieved = set(word2vec_retrieved) & relevant_verses
            
            # Hitung metrik
            word2vec_precision = len(word2vec_relevant_retrieved) / len(word2vec_retrieved) if word2vec_retrieved else 0
            word2vec_recall = len(word2vec_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
            word2vec_f1 = 2 * (word2vec_precision * word2vec_recall) / (word2vec_precision + word2vec_recall) if (word2vec_precision + word2vec_recall) > 0 else 0
            
            results['word2vec'][threshold]['precision'].append(word2vec_precision)
            results['word2vec'][threshold]['recall'].append(word2vec_recall)
            results['word2vec'][threshold]['f1_score'].append(word2vec_f1)
            results['word2vec'][threshold]['result_count'].append(len(word2vec_retrieved))
            
            print(f"      Word2Vec - {len(word2vec_retrieved)} hasil, P: {word2vec_precision:.4f}, R: {word2vec_recall:.4f}, F1: {word2vec_f1:.4f}")
            
            # FastText
            fasttext_results = fasttext_model.search(query, threshold=threshold, limit=100)
            
            # Ekstrak ID ayat dari hasil
            fasttext_retrieved = [f"{r['surah_number']}:{r['ayat_number']}" for r in fasttext_results]
            fasttext_relevant_retrieved = set(fasttext_retrieved) & relevant_verses
            
            # Hitung metrik
            fasttext_precision = len(fasttext_relevant_retrieved) / len(fasttext_retrieved) if fasttext_retrieved else 0
            fasttext_recall = len(fasttext_relevant_retrieved) / len(relevant_verses) if relevant_verses else 0
            fasttext_f1 = 2 * (fasttext_precision * fasttext_recall) / (fasttext_precision + fasttext_recall) if (fasttext_precision + fasttext_recall) > 0 else 0
            
            results['fasttext'][threshold]['precision'].append(fasttext_precision)
            results['fasttext'][threshold]['recall'].append(fasttext_recall)
            results['fasttext'][threshold]['f1_score'].append(fasttext_f1)
            results['fasttext'][threshold]['result_count'].append(len(fasttext_retrieved))
            
            print(f"      FastText - {len(fasttext_retrieved)} hasil, P: {fasttext_precision:.4f}, R: {fasttext_recall:.4f}, F1: {fasttext_f1:.4f}")
    
    return results

def print_embedding_algorithm_results(results):
    """
    Menampilkan hasil eksperimen algoritma embedding
    """
    print("\n=== HASIL EKSPERIMEN ALGORITMA EMBEDDING AYAT ===")
    
    # Untuk setiap model (Word2Vec dan FastText)
    for model_name in ['word2vec', 'fasttext']:
        print(f"\nModel: {model_name.upper()}")
        
        # Siapkan data tabel
        table_data = []
        
        # Header
        headers = ["Algoritma", "Precision", "Recall", "F1-Score", "Waktu Eksekusi (s)"]
        
        # Untuk setiap algoritma embedding
        for algo_name, metrics in results[model_name].items():
            # Hitung rata-rata metrik
            avg_precision = np.mean(metrics['precision'])
            avg_recall = np.mean(metrics['recall'])
            avg_f1_score = np.mean(metrics['f1_score'])
            avg_execution_time = np.mean(metrics['execution_time'])
            
            # Tambahkan ke tabel
            table_data.append([
                algo_name,
                f"{avg_precision:.4f}",
                f"{avg_recall:.4f}",
                f"{avg_f1_score:.4f}",
                f"{avg_execution_time:.4f}"
            ])
        
        # Tampilkan tabel
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Simpan hasil ke file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/optimization')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'embedding_algorithm_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

def print_threshold_results(results):
    """
    Menampilkan hasil eksperimen threshold kesamaan kosinus
    """
    print("\n=== HASIL EKSPERIMEN THRESHOLD KESAMAAN KOSINUS ===")
    
    # Untuk setiap model (Word2Vec dan FastText)
    for model_name in ['word2vec', 'fasttext']:
        print(f"\nModel: {model_name.upper()}")
        
        # Siapkan data tabel
        table_data = []
        
        # Header
        headers = ["Threshold", "Precision", "Recall", "F1-Score", "Jumlah Hasil Rata-rata"]
        
        # Untuk setiap threshold
        for threshold, metrics in results[model_name].items():
            # Hitung rata-rata metrik
            avg_precision = np.mean(metrics['precision'])
            avg_recall = np.mean(metrics['recall'])
            avg_f1_score = np.mean(metrics['f1_score'])
            avg_result_count = np.mean(metrics['result_count'])
            
            # Tambahkan ke tabel
            table_data.append([
                threshold,
                f"{avg_precision:.4f}",
                f"{avg_recall:.4f}",
                f"{avg_f1_score:.4f}",
                f"{avg_result_count:.1f}"
            ])
        
        # Tampilkan tabel
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Simpan hasil ke file
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/optimization')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, 'threshold_results.json'), 'w') as f:
        json.dump(results, f, indent=2)

def plot_embedding_algorithm_results(results):
    """
    Membuat visualisasi hasil eksperimen algoritma embedding
    """
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/optimization')
    os.makedirs(output_dir, exist_ok=True)
    
    # Persiapkan data
    algorithms = list(results['word2vec'].keys())
    metrics = ['precision', 'recall', 'f1_score']
    metric_labels = ['Precision', 'Recall', 'F1-Score']
    
    # Buat grafik untuk setiap metrik
    for i, metric in enumerate(metrics):
        plt.figure(figsize=(10, 6))
        
        # Data Word2Vec
        w2v_values = [np.mean(results['word2vec'][algo][metric]) for algo in algorithms]
        
        # Data FastText
        ft_values = [np.mean(results['fasttext'][algo][metric]) for algo in algorithms]
        
        # Posisi bar
        x = np.arange(len(algorithms))
        width = 0.35
        
        # Plot bar
        plt.bar(x - width/2, w2v_values, width, label='Word2Vec')
        plt.bar(x + width/2, ft_values, width, label='FastText')
        
        # Label dan judul
        plt.xlabel('Algoritma Embedding')
        plt.ylabel(metric_labels[i])
        plt.title(f'Perbandingan {metric_labels[i]} Antar Algoritma Embedding')
        plt.xticks(x, algorithms)
        plt.legend()
        
        # Simpan grafik
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'embedding_{metric}.png'))
    
    # Grafik waktu eksekusi
    plt.figure(figsize=(10, 6))
    
    # Data Word2Vec
    w2v_times = [np.mean(results['word2vec'][algo]['execution_time']) for algo in algorithms]
    
    # Data FastText
    ft_times = [np.mean(results['fasttext'][algo]['execution_time']) for algo in algorithms]
    
    # Posisi bar
    x = np.arange(len(algorithms))
    width = 0.35
    
    # Plot bar
    plt.bar(x - width/2, w2v_times, width, label='Word2Vec')
    plt.bar(x + width/2, ft_times, width, label='FastText')
    
    # Label dan judul
    plt.xlabel('Algoritma Embedding')
    plt.ylabel('Waktu Eksekusi (detik)')
    plt.title('Perbandingan Waktu Eksekusi Antar Algoritma Embedding')
    plt.xticks(x, algorithms)
    plt.legend()
    
    # Simpan grafik
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'embedding_execution_time.png'))
    
    print(f"\nGrafik perbandingan algoritma embedding disimpan di direktori '{output_dir}'")

def plot_threshold_results(results):
    """
    Membuat visualisasi hasil eksperimen threshold kesamaan kosinus
    """
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results/optimization')
    os.makedirs(output_dir, exist_ok=True)
    
    # Persiapkan data
    thresholds = [float(t) for t in results['word2vec'].keys()]
    thresholds.sort()
    
    # Grafik metrik (Precision, Recall, F1-Score)
    plt.figure(figsize=(10, 6))
    
    # Plot Word2Vec
    plt.subplot(1, 2, 1)
    plt.plot(thresholds, [np.mean(results['word2vec'][str(t)]['precision']) for t in thresholds], 'o-', label='Precision')
    plt.plot(thresholds, [np.mean(results['word2vec'][str(t)]['recall']) for t in thresholds], 's-', label='Recall')
    plt.plot(thresholds, [np.mean(results['word2vec'][str(t)]['f1_score']) for t in thresholds], '^-', label='F1-Score')
    
    plt.xlabel('Threshold')
    plt.ylabel('Nilai Metrik')
    plt.title('Word2Vec - Pengaruh Threshold Terhadap Metrik')
    plt.grid(True)
    plt.legend()
    
    # Plot FastText
    plt.subplot(1, 2, 2)
    plt.plot(thresholds, [np.mean(results['fasttext'][str(t)]['precision']) for t in thresholds], 'o-', label='Precision')
    plt.plot(thresholds, [np.mean(results['fasttext'][str(t)]['recall']) for t in thresholds], 's-', label='Recall')
    plt.plot(thresholds, [np.mean(results['fasttext'][str(t)]['f1_score']) for t in thresholds], '^-', label='F1-Score')
    
    plt.xlabel('Threshold')
    plt.ylabel('Nilai Metrik')
    plt.title('FastText - Pengaruh Threshold Terhadap Metrik')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'threshold_metrics.png'))
    
    # Grafik jumlah hasil
    plt.figure(figsize=(10, 5))
    
    plt.plot(thresholds, [np.mean(results['word2vec'][str(t)]['result_count']) for t in thresholds], 'o-', label='Word2Vec')
    plt.plot(thresholds, [np.mean(results['fasttext'][str(t)]['result_count']) for t in thresholds], 's-', label='FastText')
    
    plt.xlabel('Threshold')
    plt.ylabel('Jumlah Hasil Rata-rata')
    plt.title('Pengaruh Threshold Terhadap Jumlah Hasil')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'threshold_result_count.png'))
    
    print(f"\nGrafik perbandingan threshold disimpan di direktori '{output_dir}'")

def main():
    """
    Fungsi utama
    """
    print("=== OPTIMASI MODEL PENCARIAN SEMANTIK AL-QURAN ===")
    
    try:
        # Muat model
        word2vec_model, fasttext_model = load_models()
        
        # Muat benchmark dataset
        benchmark_data = load_benchmark_dataset()
        
        # Ekstrak query dan ayat relevan
        queries = [item['query'] for item in benchmark_data]
        relevant_verses_dict = {item['query']: item['relevant_verses'] for item in benchmark_data}
        
        # Muat data Al-Quran yang sudah diproses
        dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_path)
        
        # Menu eksperimen
        print("\nPilih eksperimen yang akan dijalankan:")
        print("1. Variasi algoritma embedding ayat")
        print("2. Variasi threshold kesamaan kosinus")
        print("3. Kedua eksperimen")
        
        choice = input("Pilihan (1/2/3): ")
        
        if choice in ['1', '3']:
            # Eksperimen algoritma embedding ayat
            embedding_results = experiment_embedding_algorithms(
                word2vec_model, fasttext_model, preprocessed_verses, queries, relevant_verses_dict
            )
            
            # Tampilkan hasil
            print_embedding_algorithm_results(embedding_results)
            
            # Buat visualisasi
            plot_embedding_algorithm_results(embedding_results)
        
        if choice in ['2', '3']:
            # Eksperimen threshold kesamaan kosinus
            threshold_results = experiment_threshold_variation(
                word2vec_model, fasttext_model, queries, relevant_verses_dict
            )
            
            # Tampilkan hasil
            print_threshold_results(threshold_results)
            
            # Buat visualisasi
            plot_threshold_results(threshold_results)
    
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 