"""
Script runner untuk semua task Fase 2: Peningkatan Metode Agregasi FastText
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FastTextPhase2Runner:
    """
    Runner untuk semua task Fase 2: Peningkatan Metode Agregasi
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.scripts_dir = os.path.join(self.base_dir, 'scripts')
        self.results_dir = os.path.join(self.base_dir, 'results')
        
        # Task yang akan dijalankan
        self.tasks = {
            '2.1': 'Implementasi Weighted Pooling',
            '2.2': 'Implementasi Attention Mechanism', 
            '2.3': 'Eksperimen dan Evaluasi',
            '2.4': 'Integrasi dengan Sistem Utama'
        }
        
        # Status task
        self.task_status = {}
        
    def run_task_2_1(self) -> bool:
        """
        Task 2.1: Implementasi Weighted Pooling
        """
        print("\n=== TASK 2.1: IMPLEMENTASI WEIGHTED POOLING ===")
        
        try:
            # Cek apakah modul weighted pooling sudah dibuat
            weighted_pooling_path = os.path.join(self.base_dir, 'backend/weighted_pooling.py')
            if not os.path.exists(weighted_pooling_path):
                print("❌ Modul weighted_pooling.py belum dibuat")
                return False
            
            print("✅ Modul weighted_pooling.py sudah dibuat")
            
            # Test import modul
            try:
                from backend.weighted_pooling import WeightedPooling, FastTextWeightedPooling
                print("✅ Import modul weighted pooling berhasil")
            except Exception as e:
                print(f"❌ Error importing weighted pooling: {e}")
                return False
            
            # Test metode weighted pooling
            print("Testing weighted pooling methods...")
            methods = ['tfidf', 'frequency', 'position', 'hybrid']
            
            for method in methods:
                try:
                    pooling = WeightedPooling(method=method)
                    print(f"✅ {method} pooling method created successfully")
                except Exception as e:
                    print(f"❌ Error creating {method} pooling: {e}")
                    return False
            
            print("✅ Task 2.1 selesai!")
            return True
            
        except Exception as e:
            print(f"✗ Error pada Task 2.1: {e}")
            return False
    
    def run_task_2_2(self) -> bool:
        """
        Task 2.2: Implementasi Attention Mechanism
        """
        print("\n=== TASK 2.2: IMPLEMENTASI ATTENTION MECHANISM ===")
        
        try:
            # Cek apakah modul attention embedding sudah dibuat
            attention_path = os.path.join(self.base_dir, 'backend/attention_embedding.py')
            if not os.path.exists(attention_path):
                print("❌ Modul attention_embedding.py belum dibuat")
                return False
            
            print("✅ Modul attention_embedding.py sudah dibuat")
            
            # Test import modul
            try:
                from backend.attention_embedding import SelfAttention, AttentionEmbedding, FastTextAttentionEmbedding
                print("✅ Import modul attention embedding berhasil")
            except Exception as e:
                print(f"❌ Error importing attention embedding: {e}")
                return False
            
            # Test attention mechanism
            print("Testing attention mechanism...")
            try:
                attention = SelfAttention(vector_dim=200, attention_dim=64)
                print("✅ SelfAttention created successfully")
            except Exception as e:
                print(f"❌ Error creating SelfAttention: {e}")
                return False
            
            print("✅ Task 2.2 selesai!")
            return True
            
        except Exception as e:
            print(f"✗ Error pada Task 2.2: {e}")
            return False
    
    def run_task_2_3(self) -> bool:
        """
        Task 2.3: Eksperimen dan Evaluasi
        """
        print("\n=== TASK 2.3: EKSPERIMEN DAN EVALUASI ===")
        
        try:
            # Cek apakah script eksperimen sudah dibuat
            experiment_script = os.path.join(self.scripts_dir, 'fasttext_aggregation_experiment.py')
            if not os.path.exists(experiment_script):
                print("❌ Script eksperimen belum dibuat")
                return False
            
            print("✅ Script eksperimen sudah dibuat")
            
            # Jalankan eksperimen
            print("Running aggregation experiment...")
            result = subprocess.run([sys.executable, experiment_script], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                print("✅ Eksperimen agregasi berhasil dijalankan")
                print("📊 Hasil eksperimen tersimpan di direktori results/")
            else:
                print(f"❌ Error menjalankan eksperimen: {result.stderr}")
                return False
            
            print("✅ Task 2.3 selesai!")
            return True
            
        except Exception as e:
            print(f"✗ Error pada Task 2.3: {e}")
            return False
    
    def run_task_2_4(self) -> bool:
        """
        Task 2.4: Integrasi dengan Sistem Utama
        """
        print("\n=== TASK 2.4: INTEGRASI DENGAN SISTEM UTAMA ===")
        
        try:
            # Cek apakah script optimasi sudah dibuat
            optimization_script = os.path.join(self.scripts_dir, 'update_fasttext_aggregation.py')
            if not os.path.exists(optimization_script):
                print("❌ Script optimasi belum dibuat")
                return False
            
            print("✅ Script optimasi sudah dibuat")
            
            # Cek apakah ada hasil eksperimen
            experiment_files = []
            if os.path.exists(self.results_dir):
                for filename in os.listdir(self.results_dir):
                    if filename.startswith('fasttext_aggregation_experiment_') and filename.endswith('.json'):
                        experiment_files.append(filename)
            
            if not experiment_files:
                print("⚠️ Tidak ada hasil eksperimen yang ditemukan")
                print("   Jalankan Task 2.3 terlebih dahulu")
                return False
            
            print(f"✅ Ditemukan {len(experiment_files)} file hasil eksperimen")
            
            # Jalankan optimasi
            print("Running model optimization...")
            result = subprocess.run([sys.executable, optimization_script], 
                                  capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                print("✅ Optimasi model berhasil dijalankan")
                print("🏆 Model optimal tersimpan")
            else:
                print(f"❌ Error menjalankan optimasi: {result.stderr}")
                return False
            
            print("✅ Task 2.4 selesai!")
            return True
            
        except Exception as e:
            print(f"✗ Error pada Task 2.4: {e}")
            return False
    
    def run_all_tasks(self) -> bool:
        """
        Jalankan semua task Fase 2
        """
        print("=== FastText Phase 2: Peningkatan Metode Agregasi ===")
        print(f"Total tasks: {len(self.tasks)}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # Jalankan task secara berurutan
        task_results = {}
        
        for task_id, task_name in self.tasks.items():
            print(f"\n{'='*50}")
            print(f"Running Task {task_id}: {task_name}")
            print(f"{'='*50}")
            
            try:
                if task_id == '2.1':
                    success = self.run_task_2_1()
                elif task_id == '2.2':
                    success = self.run_task_2_2()
                elif task_id == '2.3':
                    success = self.run_task_2_3()
                elif task_id == '2.4':
                    success = self.run_task_2_4()
                else:
                    print(f"❌ Unknown task: {task_id}")
                    success = False
                
                task_results[task_id] = {
                    'name': task_name,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                }
                
                if success:
                    print(f"✅ Task {task_id} completed successfully")
                else:
                    print(f"❌ Task {task_id} failed")
                
            except Exception as e:
                print(f"❌ Error in Task {task_id}: {e}")
                task_results[task_id] = {
                    'name': task_name,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Hitung waktu total
        total_time = time.time() - start_time
        
        # Buat laporan
        self._create_report(task_results, total_time)
        
        # Tampilkan ringkasan
        self._print_summary(task_results, total_time)
        
        return all(result['success'] for result in task_results.values())
    
    def _create_report(self, task_results: Dict[str, Any], total_time: float):
        """
        Buat laporan hasil eksekusi
        """
        report = {
            'phase': '2',
            'title': 'FastText Phase 2: Peningkatan Metode Agregasi',
            'timestamp': datetime.now().isoformat(),
            'total_time': total_time,
            'task_results': task_results,
            'summary': {
                'total_tasks': len(task_results),
                'completed_tasks': sum(1 for r in task_results.values() if r['success']),
                'failed_tasks': sum(1 for r in task_results.values() if not r['success']),
                'success_rate': sum(1 for r in task_results.values() if r['success']) / len(task_results)
            }
        }
        
        # Simpan laporan
        os.makedirs(self.results_dir, exist_ok=True)
        report_path = os.path.join(self.results_dir, f'fasttext_phase2_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Report saved: {report_path}")
    
    def _print_summary(self, task_results: Dict[str, Any], total_time: float):
        """
        Cetak ringkasan hasil
        """
        print(f"\n{'='*60}")
        print("📊 PHASE 2 EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        completed = sum(1 for r in task_results.values() if r['success'])
        failed = len(task_results) - completed
        
        print(f"Total Tasks: {len(task_results)}")
        print(f"Completed: {completed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {completed/len(task_results)*100:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        
        print(f"\n📋 Task Details:")
        for task_id, result in task_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} Task {task_id}: {result['name']}")
            if not result['success'] and 'error' in result:
                print(f"     Error: {result['error']}")
        
        if completed == len(task_results):
            print(f"\n🎉 All tasks completed successfully!")
            print("🚀 FastText Phase 2 ready for production")
        else:
            print(f"\n⚠️ Some tasks failed. Please check the errors above.")


def main():
    """
    Main function
    """
    runner = FastTextPhase2Runner()
    
    try:
        success = runner.run_all_tasks()
        
        if success:
            print("\n✅ FastText Phase 2 completed successfully!")
            print("🚀 Ready for Phase 3: Domain Adaptation")
        else:
            print("\n❌ FastText Phase 2 completed with errors")
            print("🔧 Please check the task results above")
        
    except Exception as e:
        print(f"❌ Error during Phase 2 execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 