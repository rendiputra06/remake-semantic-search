import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

EXPERIMENT_SCRIPT = os.path.join(SCRIPTS_DIR, 'fasttext_aggregation_experiment.py')
OPTIMIZE_SCRIPT = os.path.join(SCRIPTS_DIR, 'update_fasttext_aggregation.py')


def run_experiment():
    print("\n=== [AUTO-TUNE] Menjalankan eksperimen agregasi FastText ===")
    result = subprocess.run([sys.executable, EXPERIMENT_SCRIPT], capture_output=True, text=True, cwd=BASE_DIR)
    print(result.stdout)
    if result.returncode != 0:
        print("[ERROR] Gagal menjalankan eksperimen agregasi!")
        print(result.stderr)
        return False
    print("[OK] Eksperimen agregasi selesai.")
    return True

def run_optimization():
    print("\n=== [AUTO-TUNE] Menjalankan optimasi & update config default ===")
    result = subprocess.run([sys.executable, OPTIMIZE_SCRIPT], capture_output=True, text=True, cwd=BASE_DIR)
    print(result.stdout)
    if result.returncode != 0:
        print("[ERROR] Gagal menjalankan optimasi!")
        print(result.stderr)
        return False
    print("[OK] Optimasi & update config selesai.")
    return True


def main():
    print("\n=== AUTO-TUNING FASTTEXT AGGREGATION (END-TO-END) ===")
    ok1 = run_experiment()
    if not ok1:
        print("[FATAL] Auto-tuning dihentikan karena eksperimen gagal.")
        return
    ok2 = run_optimization()
    if not ok2:
        print("[FATAL] Auto-tuning dihentikan karena optimasi gagal.")
        return
    print("\n=== AUTO-TUNING SELESAI! ===")
    print("Cek hasil di folder results/ dan config di models/fasttext/system_integration.json")

if __name__ == "__main__":
    main() 