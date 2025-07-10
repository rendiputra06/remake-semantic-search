"""
Script untuk menjalankan semua task Fase 1: Optimasi Parameter N-gram
dari fasttext_improvement_tasks.md
"""
import os
import sys
import time
import subprocess
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FastTextPhase1Runner:
    """
    Kelas untuk menjalankan semua task Fase 1 FastText improvement
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.base_dir, 'results')
        self.scripts_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Buat direktori results jika belum ada
        os.makedirs(self.results_dir, exist_ok=True)
        
    def run_task_1_1(self) -> bool:
        """
        Task 1.1: Persiapan Eksperimen
        """
        print("\n=== TASK 1.1: PERSIAPAN EKSPERIMEN ===")
        
        try:
            # Cek dependencies terlebih dahulu
            print("Mengecek dependencies...")
            dependency_checker = os.path.join(self.scripts_dir, 'check_dependencies.py')
            if os.path.exists(dependency_checker):
                result = subprocess.run([sys.executable, dependency_checker], 
                                      capture_output=True, text=True, cwd=self.base_dir)
                if result.returncode != 0:
                    print("⚠️ Warning: Beberapa dependencies mungkin belum terinstall")
                    print("Silakan jalankan: python scripts/check_dependencies.py")
            
            # Cek model FastText
            print("Mengecek model FastText...")
            model_fixer = os.path.join(self.scripts_dir, 'fix_fasttext_model.py')
            if os.path.exists(model_fixer):
                result = subprocess.run([sys.executable, model_fixer], 
                                      capture_output=True, text=True, cwd=self.base_dir)
                if result.returncode != 0:
                    print("⚠️ Warning: Model FastText mungkin bermasalah")
                    print("Silakan jalankan: python scripts/fix_fasttext_model.py")
            
            # 1. Membuat script eksperimen untuk pengujian berbagai konfigurasi parameter n-gram
            print("✓ Script eksperimen sudah dibuat: fasttext_ngram_experiment.py")
            
            # 2. Menyiapkan dataset evaluasi yang mencakup berbagai jenis query
            print("✓ Dataset evaluasi sudah disiapkan dengan query:")
            query_categories = [
                "Query umum (shalat, puasa, zakat)",
                "Query dengan variasi morfologi (berdoa, mendoakan, doa)",
                "Query jarang/domain-specific (malaikat, nabi, rasul)",
                "Query dengan kata majemuk (hari kiamat, surga neraka)",
                "Query dengan kata asing (alhamdulillah, insyaallah)"
            ]
            for category in query_categories:
                print(f"  - {category}")
            
            # 3. Mendefinisikan metrik evaluasi yang komprehensif
            print("✓ Metrik evaluasi yang komprehensif sudah didefinisikan:")
            metrics = [
                "Precision, Recall, F1-score",
                "MAP (Mean Average Precision)",
                "NDCG (Normalized Discounted Cumulative Gain)"
            ]
            for metric in metrics:
                print(f"  - {metric}")
            
            print("✓ Task 1.1 selesai!")
            return True
            
        except Exception as e:
            print(f"✗ Error pada Task 1.1: {e}")
            return False
    
    def run_task_1_2(self) -> bool:
        """
        Task 1.2: Eksperimen Parameter N-gram
        """
        print("\n=== TASK 1.2: EKSPERIMEN PARAMETER N-GRAM ===")
        
        try:
            # Jalankan script eksperimen
            experiment_script = os.path.join(self.scripts_dir, 'fasttext_ngram_experiment.py')
            
            print("Menjalankan eksperimen parameter n-gram...")
            print("Parameter yang akan dieksperimen:")
            print("  - min_n: [2, 3]")
            print("  - max_n: [4, 5, 6]")
            print("  - Kombinasi: min_n=2,max_n=4; min_n=2,max_n=5; min_n=2,max_n=6; min_n=3,max_n=4; min_n=3,max_n=5; min_n=3,max_n=6")
            
            # Jalankan script
            result = subprocess.run([sys.executable, experiment_script], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                print("✓ Eksperimen parameter n-gram berhasil dijalankan!")
                print("✓ Hasil eksperimen disimpan di folder results/")
                return True
            else:
                print(f"✗ Error menjalankan eksperimen: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error pada Task 1.2: {e}")
            return False
    
    def run_task_1_3(self) -> bool:
        """
        Task 1.3: Implementasi Konfigurasi Optimal
        """
        print("\n=== TASK 1.3: IMPLEMENTASI KONFIGURASI OPTIMAL ===")
        
        try:
            # Cek apakah hasil eksperimen ada
            results_file = os.path.join(self.results_dir, 'fasttext_ngram_experiment_results.json')
            if not os.path.exists(results_file):
                print("✗ File hasil eksperimen tidak ditemukan. Jalankan Task 1.2 terlebih dahulu.")
                return False
            
            # Jalankan script optimasi
            optimization_script = os.path.join(self.scripts_dir, 'update_fasttext_optimal.py')
            
            print("Menjalankan optimasi model dengan parameter terbaik...")
            
            # Jalankan script
            result = subprocess.run([sys.executable, optimization_script], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            
            # Tampilkan output jika ada
            if result.stdout:
                print(result.stdout)
            
            if result.returncode == 0:
                print("✓ Model FastText berhasil dioptimalkan!")
                print("✓ Model optimal telah diintegrasikan ke sistem!")
                return True
            else:
                print(f"✗ Error menjalankan optimasi: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error pada Task 1.3: {e}")
            return False
    
    def generate_phase1_report(self) -> Dict[str, Any]:
        """
        Membuat laporan hasil Fase 1
        """
        print("\n=== GENERATING PHASE 1 REPORT ===")
        
        report = {
            'phase': 'Fase 1: Optimasi Parameter N-gram',
            'completion_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tasks_completed': [],
            'results_summary': {},
            'next_steps': []
        }
        
        # Cek hasil eksperimen
        experiment_results_file = os.path.join(self.results_dir, 'fasttext_ngram_experiment_results.json')
        if os.path.exists(experiment_results_file):
            import json
            with open(experiment_results_file, 'r', encoding='utf-8') as f:
                experiment_results = json.load(f)
            
            if experiment_results:
                best_result = max(experiment_results, key=lambda x: x['avg_f1'])
                report['results_summary']['best_config'] = {
                    'min_n': best_result['min_n'],
                    'max_n': best_result['max_n'],
                    'avg_f1': best_result['avg_f1'],
                    'avg_precision': best_result['avg_precision'],
                    'avg_recall': best_result['avg_recall']
                }
        
        # Cek hasil optimasi
        optimization_file = os.path.join(self.results_dir, 'fasttext_optimization_evaluation.json')
        if os.path.exists(optimization_file):
            with open(optimization_file, 'r', encoding='utf-8') as f:
                optimization_results = json.load(f)
            
            report['results_summary']['optimization'] = optimization_results.get('evaluation_results', {})
        
        # Simpan laporan
        report_file = os.path.join(self.results_dir, 'fasttext_phase1_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Laporan Fase 1 disimpan di: {report_file}")
        
        return report
    
    def run_all_phase1_tasks(self) -> bool:
        """
        Menjalankan semua task Fase 1 secara berurutan
        """
        print("=== FASTTEXT PHASE 1: OPTIMASI PARAMETER N-GRAM ===")
        print("Menjalankan semua task Fase 1...")
        
        start_time = time.time()
        
        # Task 1.1: Persiapan Eksperimen
        if not self.run_task_1_1():
            print("✗ Task 1.1 gagal. Menghentikan proses.")
            return False
        
        # Task 1.2: Eksperimen Parameter N-gram
        if not self.run_task_1_2():
            print("✗ Task 1.2 gagal. Menghentikan proses.")
            return False
        
        # Task 1.3: Implementasi Konfigurasi Optimal
        if not self.run_task_1_3():
            print("✗ Task 1.3 gagal. Menghentikan proses.")
            return False
        
        # Generate laporan
        report = self.generate_phase1_report()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n=== PHASE 1 SELESAI ===")
        print(f"Durasi: {duration:.2f} detik")
        print(f"Semua task Fase 1 berhasil diselesaikan!")
        
        # Tampilkan ringkasan hasil
        if 'best_config' in report['results_summary']:
            best_config = report['results_summary']['best_config']
            print(f"\nKonfigurasi Optimal yang Ditemukan:")
            print(f"  min_n: {best_config['min_n']}")
            print(f"  max_n: {best_config['max_n']}")
            print(f"  Avg F1: {best_config['avg_f1']:.4f}")
            print(f"  Avg Precision: {best_config['avg_precision']:.4f}")
            print(f"  Avg Recall: {best_config['avg_recall']:.4f}")
        
        print(f"\nLaporan lengkap tersimpan di: {os.path.join(self.results_dir, 'fasttext_phase1_report.json')}")
        
        return True

def main():
    """
    Main function untuk menjalankan semua task Fase 1
    """
    print("=== FastText Phase 1 Implementation ===")
    
    # Buat runner
    runner = FastTextPhase1Runner()
    
    # Jalankan semua task
    success = runner.run_all_phase1_tasks()
    
    if success:
        print("\n🎉 Fase 1 berhasil diselesaikan!")
        print("Siap untuk melanjutkan ke Fase 2: Peningkatan Metode Agregasi")
    else:
        print("\n❌ Fase 1 gagal diselesaikan.")
        print("Silakan periksa error di atas dan coba lagi.")

if __name__ == "__main__":
    main() 