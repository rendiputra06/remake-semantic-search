"""
Script untuk membandingkan performa antara model Word2Vec dan FastText
"""
import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

# Tambahkan direktori parent ke path agar import berfungsi dengan benar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import setelah mengatur path
from backend.word2vec_model import Word2VecModel
from backend.fasttext_model import FastTextModel

def load_models():
    """
    Memuat model Word2Vec dan FastText beserta vektor ayat yang sudah disimpan
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
    
    return word2vec_model, fasttext_model

def compare_search_results(word2vec_model, fasttext_model, queries, threshold=0.5, limit=10):
    """
    Membandingkan hasil pencarian dari model Word2Vec dan FastText
    
    Args:
        word2vec_model: Model Word2Vec
        fasttext_model: Model FastText
        queries: List query untuk uji coba
        threshold: Threshold untuk kesamaan kosinus
        limit: Jumlah hasil maksimal per query
    
    Returns:
        Dict dengan hasil perbandingan
    """
    results = {
        'word2vec': {
            'times': [],
            'result_counts': [],
            'similarity_scores': []
        },
        'fasttext': {
            'times': [],
            'result_counts': [],
            'similarity_scores': []
        }
    }
    
    print("\nMembandingkan hasil pencarian...")
    print("-" * 50)
    
    for i, query in enumerate(queries):
        print(f"Query {i+1}: '{query}'")
        
        # Word2Vec
        start_time = time.time()
        word2vec_results = word2vec_model.search(query, threshold=threshold, limit=limit)
        word2vec_time = time.time() - start_time
        
        results['word2vec']['times'].append(word2vec_time)
        results['word2vec']['result_counts'].append(len(word2vec_results))
        
        if word2vec_results:
            avg_similarity = sum(r['similarity'] for r in word2vec_results) / len(word2vec_results)
            top_similarity = word2vec_results[0]['similarity'] if word2vec_results else 0
            results['word2vec']['similarity_scores'].append((top_similarity, avg_similarity))
        else:
            results['word2vec']['similarity_scores'].append((0, 0))
        
        # FastText
        start_time = time.time()
        fasttext_results = fasttext_model.search(query, threshold=threshold, limit=limit)
        fasttext_time = time.time() - start_time
        
        results['fasttext']['times'].append(fasttext_time)
        results['fasttext']['result_counts'].append(len(fasttext_results))
        
        if fasttext_results:
            avg_similarity = sum(r['similarity'] for r in fasttext_results) / len(fasttext_results)
            top_similarity = fasttext_results[0]['similarity'] if fasttext_results else 0
            results['fasttext']['similarity_scores'].append((top_similarity, avg_similarity))
        else:
            results['fasttext']['similarity_scores'].append((0, 0))
        
        # Tampilkan perbandingan sederhana
        print(f"  Word2Vec: {len(word2vec_results)} hasil, waktu: {word2vec_time:.4f} detik")
        print(f"  FastText: {len(fasttext_results)} hasil, waktu: {fasttext_time:.4f} detik")
        print("-" * 50)
    
    return results

def print_comparison_table(results, queries):
    """
    Menampilkan tabel perbandingan hasil
    """
    table_data = []
    
    for i, query in enumerate(queries):
        row = [
            i+1,
            query,
            f"{results['word2vec']['result_counts'][i]}",
            f"{results['fasttext']['result_counts'][i]}",
            f"{results['word2vec']['times'][i]:.4f}s",
            f"{results['fasttext']['times'][i]:.4f}s",
            f"{results['word2vec']['similarity_scores'][i][0]:.4f}",
            f"{results['fasttext']['similarity_scores'][i][0]:.4f}"
        ]
        table_data.append(row)
    
    # Tambahkan rata-rata
    avg_row = [
        "",
        "RATA-RATA",
        f"{np.mean(results['word2vec']['result_counts']):.2f}",
        f"{np.mean(results['fasttext']['result_counts']):.2f}",
        f"{np.mean(results['word2vec']['times']):.4f}s",
        f"{np.mean(results['fasttext']['times']):.4f}s",
        f"{np.mean([s[0] for s in results['word2vec']['similarity_scores']]):.4f}",
        f"{np.mean([s[0] for s in results['fasttext']['similarity_scores']]):.4f}"
    ]
    table_data.append(avg_row)
    
    headers = [
        "No", 
        "Query", 
        "W2V Count", 
        "FT Count", 
        "W2V Time", 
        "FT Time", 
        "W2V Top Sim", 
        "FT Top Sim"
    ]
    
    print("\nTabel Perbandingan Performa:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def plot_comparison(results, queries):
    """
    Membuat visualisasi perbandingan hasil
    """
    # Siapkan data
    x = np.arange(len(queries))
    width = 0.35
    
    # Plot waktu eksekusi
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width/2, results['word2vec']['times'], width, label='Word2Vec')
    ax.bar(x + width/2, results['fasttext']['times'], width, label='FastText')
    
    ax.set_title('Perbandingan Waktu Eksekusi')
    ax.set_ylabel('Waktu (detik)')
    ax.set_xlabel('Query')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Q{i+1}" for i in range(len(queries))])
    ax.legend()
    
    # Simpan grafik
    plt.tight_layout()
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'execution_time_comparison.png'))
    
    # Plot jumlah hasil
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width/2, results['word2vec']['result_counts'], width, label='Word2Vec')
    ax.bar(x + width/2, results['fasttext']['result_counts'], width, label='FastText')
    
    ax.set_title('Perbandingan Jumlah Hasil')
    ax.set_ylabel('Jumlah Hasil')
    ax.set_xlabel('Query')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Q{i+1}" for i in range(len(queries))])
    ax.legend()
    
    # Simpan grafik
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'result_count_comparison.png'))
    
    # Plot skor kesamaan teratas
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width/2, [s[0] for s in results['word2vec']['similarity_scores']], width, label='Word2Vec')
    ax.bar(x + width/2, [s[0] for s in results['fasttext']['similarity_scores']], width, label='FastText')
    
    ax.set_title('Perbandingan Skor Kesamaan Teratas')
    ax.set_ylabel('Skor Kesamaan')
    ax.set_xlabel('Query')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Q{i+1}" for i in range(len(queries))])
    ax.legend()
    
    # Simpan grafik
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'top_similarity_comparison.png'))
    
    print(f"\nGrafik perbandingan disimpan di direktori '{output_dir}'")

def main():
    """
    Fungsi utama
    """
    print("=== PERBANDINGAN MODEL WORD2VEC DAN FASTTEXT ===")
    
    # Daftar query untuk pengujian
    test_queries = [
        "berdoa kepada Allah",
        "jalan yang lurus",
        "rezeki yang halal",
        "hari kiamat",
        "surga dan neraka",
        "perintah sholat",
        "berbuat baik pada orang tua",
        "sedekah kepada fakir miskin",
        "sabar menghadapi cobaan",
        "taubat dari dosa"
    ]
    
    try:
        # Muat model
        word2vec_model, fasttext_model = load_models()
        
        # Bandingkan hasil pencarian
        comparison_results = compare_search_results(word2vec_model, fasttext_model, test_queries)
        
        # Tampilkan tabel perbandingan
        print_comparison_table(comparison_results, test_queries)
        
        # Buat visualisasi
        plot_comparison(comparison_results, test_queries)
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 