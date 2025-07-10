"""
Script untuk mengecek dan menginstall dependencies yang dibutuhkan
untuk implementasi Fase 1: Optimasi Parameter N-gram FastText
"""
import subprocess
import sys
import os

def check_and_install_package(package_name, import_name=None):
    """
    Mengecek dan menginstall package jika belum terinstall
    
    Args:
        package_name: Nama package untuk install
        import_name: Nama untuk import (jika berbeda dengan package_name)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} sudah terinstall")
        return True
    except ImportError:
        print(f"❌ {package_name} belum terinstall, menginstall...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} berhasil diinstall")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Gagal menginstall {package_name}")
            return False

def check_dependencies():
    """
    Mengecek semua dependencies yang dibutuhkan
    """
    print("=== Pengecekan Dependencies untuk FastText Phase 1 ===")
    
    # Daftar dependencies yang dibutuhkan
    dependencies = [
        ("gensim", "gensim"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("scipy", "scipy"),
    ]
    
    all_installed = True
    
    for package_name, import_name in dependencies:
        if not check_and_install_package(package_name, import_name):
            all_installed = False
    
    if all_installed:
        print("\n✅ Semua dependencies berhasil diinstall!")
        return True
    else:
        print("\n❌ Beberapa dependencies gagal diinstall. Silakan install manual:")
        print("pip install gensim numpy pandas scikit-learn matplotlib seaborn scipy")
        return False

def check_project_structure():
    """
    Mengecek struktur project yang dibutuhkan
    """
    print("\n=== Pengecekan Struktur Project ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        "dataset/surah",
        "models/fasttext",
        "backend",
        "scripts"
    ]
    
    required_files = [
        "backend/fasttext_model.py",
        "backend/preprocessing.py",
        "backend/initialize.py"
    ]
    
    all_exist = True
    
    # Cek direktori
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if os.path.exists(full_path):
            print(f"✅ Direktori {dir_path} ada")
        else:
            print(f"❌ Direktori {dir_path} tidak ada")
            all_exist = False
    
    # Cek file
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ File {file_path} ada")
        else:
            print(f"❌ File {file_path} tidak ada")
            all_exist = False
    
    return all_exist

def check_fasttext_model():
    """
    Mengecek apakah model FastText ada
    """
    print("\n=== Pengecekan Model FastText ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models/fasttext/fasttext_model.model")
    
    if os.path.exists(model_path):
        print(f"✅ Model FastText ada di {model_path}")
        return True
    else:
        print(f"❌ Model FastText tidak ditemukan di {model_path}")
        print("💡 Anda perlu menginstall model FastText terlebih dahulu")
        return False

def main():
    """
    Main function untuk mengecek semua requirements
    """
    print("=== FastText Phase 1 - Dependency Checker ===")
    
    # Cek dependencies
    deps_ok = check_dependencies()
    
    # Cek struktur project
    structure_ok = check_project_structure()
    
    # Cek model FastText
    model_ok = check_fasttext_model()
    
    print("\n=== Ringkasan ===")
    if deps_ok and structure_ok and model_ok:
        print("✅ Semua requirements terpenuhi!")
        print("🚀 Siap untuk menjalankan FastText Phase 1")
        print("\nCara menjalankan:")
        print("python scripts/run_fasttext_phase1.py")
    else:
        print("❌ Beberapa requirements belum terpenuhi")
        if not deps_ok:
            print("- Install dependencies yang dibutuhkan")
        if not structure_ok:
            print("- Pastikan struktur project sesuai")
        if not model_ok:
            print("- Install model FastText")
        
        print("\n💡 Setelah semua requirements terpenuhi, jalankan:")
        print("python scripts/run_fasttext_phase1.py")

if __name__ == "__main__":
    main() 