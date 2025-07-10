"""
Script untuk mendiagnosis dan memperbaiki masalah model FastText
Error: operands could not be broadcast together with shapes (200,) (100,) (200,)
"""
import os
import sys
import shutil
import pickle
import numpy as np
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.preprocessing import process_quran_data

class FastTextModelFixer:
    """
    Kelas untuk mendiagnosis dan memperbaiki masalah model FastText
    """
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = os.path.join(self.base_dir, 'models/fasttext')
        self.backup_dir = os.path.join(self.base_dir, 'models/fasttext/backup')
        
    def diagnose_model(self) -> Dict[str, Any]:
        """
        Mendiagnosis masalah model FastText
        
        Returns:
            Dictionary berisi informasi diagnosis
        """
        print("=== Diagnosing FastText Model ===")
        
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        
        diagnosis = {
            'model_exists': False,
            'model_size': 0,
            'model_path': model_path,
            'error_type': None,
            'recommendation': None
        }
        
        # Cek apakah model ada
        if os.path.exists(model_path):
            diagnosis['model_exists'] = True
            diagnosis['model_size'] = os.path.getsize(model_path)
            print(f"✅ Model FastText ditemukan: {model_path}")
            print(f"📏 Ukuran file: {diagnosis['model_size']} bytes")
            
            # Coba load model untuk diagnosis lebih detail
            try:
                from gensim.models import FastText
                model = FastText.load(model_path)
                
                # Cek informasi model
                diagnosis['vector_size'] = model.vector_size
                diagnosis['vocab_size'] = len(model.wv.key_to_index)
                diagnosis['min_n'] = model.min_n
                diagnosis['max_n'] = model.max_n
                
                print(f"✅ Model berhasil dimuat")
                print(f"📊 Dimensi vektor: {diagnosis['vector_size']}")
                print(f"📚 Ukuran vocabulary: {diagnosis['vocab_size']}")
                print(f"🔤 Parameter n-gram: min_n={diagnosis['min_n']}, max_n={diagnosis['max_n']}")
                
                # Test beberapa kata
                test_words = ['allah', 'nabi', 'shalat', 'puasa']
                for word in test_words:
                    try:
                        vector = model.wv[word]
                        print(f"✅ Kata '{word}' berhasil diembed")
                    except KeyError:
                        print(f"⚠️ Kata '{word}' tidak ada dalam vocabulary")
                
                diagnosis['error_type'] = 'none'
                diagnosis['recommendation'] = 'model_ok'
                
            except Exception as e:
                error_msg = str(e)
                diagnosis['error_type'] = error_msg
                
                if 'broadcast' in error_msg.lower() or 'shapes' in error_msg.lower():
                    print(f"❌ Error: Ketidakcocokan dimensi vektor")
                    print(f"🔧 Rekomendasi: Re-train model dengan parameter yang konsisten")
                    diagnosis['recommendation'] = 'retrain_model'
                elif 'corrupt' in error_msg.lower():
                    print(f"❌ Error: Model rusak")
                    print(f"🔧 Rekomendasi: Re-download atau re-train model")
                    diagnosis['recommendation'] = 'redownload_model'
                else:
                    print(f"❌ Error: {error_msg}")
                    print(f"🔧 Rekomendasi: Periksa kompatibilitas versi gensim")
                    diagnosis['recommendation'] = 'check_compatibility'
        else:
            print(f"❌ Model FastText tidak ditemukan: {model_path}")
            diagnosis['error_type'] = 'model_not_found'
            diagnosis['recommendation'] = 'create_new_model'
        
        return diagnosis
    
    def backup_current_model(self):
        """
        Backup model saat ini
        """
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        if os.path.exists(model_path):
            os.makedirs(self.backup_dir, exist_ok=True)
            backup_path = os.path.join(self.backup_dir, f'fasttext_corrupted_{int(time.time())}.model')
            shutil.copy2(model_path, backup_path)
            print(f"📦 Model yang bermasalah dibackup ke: {backup_path}")
            return backup_path
        return None
    
    def create_new_fasttext_model(self, corpus_path: str, vector_size: int = 200) -> str:
        """
        Membuat model FastText baru
        
        Args:
            corpus_path: Path ke file korpus
            vector_size: Dimensi vektor
            
        Returns:
            Path ke model baru
        """
        from gensim.models.fasttext import FastText
        
        print(f"🔄 Membuat model FastText baru dengan dimensi {vector_size}...")
        
        # Baca korpus
        with open(corpus_path, 'r', encoding='utf-8') as f:
            sentences = [line.strip().split() for line in f if line.strip()]
        
        print(f"📚 Jumlah kalimat dalam korpus: {len(sentences)}")
        
        # Buat model baru dengan parameter yang konsisten
        model = FastText(
            sentences,
            vector_size=vector_size,
            window=5,
            min_count=1,
            min_n=2,
            max_n=5,
            workers=4,
            sg=1,  # Skip-gram
            epochs=10
        )
        
        # Simpan model
        model_path = os.path.join(self.models_dir, 'fasttext_model.model')
        os.makedirs(self.models_dir, exist_ok=True)
        model.save(model_path)
        
        print(f"✅ Model baru disimpan di: {model_path}")
        print(f"📊 Ukuran vocabulary: {len(model.wv.key_to_index)}")
        print(f"📏 Dimensi vektor: {model.vector_size}")
        
        return model_path
    
    def test_model_compatibility(self, model_path: str) -> bool:
        """
        Test kompatibilitas model
        
        Args:
            model_path: Path ke model
            
        Returns:
            True jika model kompatibel
        """
        try:
            from gensim.models import FastText
            from backend.fasttext_model import FastTextModel
            
            # Test load dengan gensim
            model = FastText.load(model_path)
            print(f"✅ Model berhasil dimuat dengan gensim")
            
            # Test dengan FastTextModel class
            fasttext_model = FastTextModel(model_path=model_path)
            fasttext_model.load_model()
            print(f"✅ Model berhasil dimuat dengan FastTextModel class")
            
            # Test dengan data Al-Quran
            dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
            preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
            
            # Ambil beberapa ayat untuk test
            test_verses = dict(list(preprocessed_verses.items())[:5])
            fasttext_model.create_verse_vectors(test_verses)
            
            print(f"✅ Model berhasil membuat vektor ayat")
            return True
            
        except Exception as e:
            print(f"❌ Error saat test kompatibilitas: {e}")
            return False
    
    def fix_model_issue(self):
        """
        Memperbaiki masalah model FastText
        """
        print("=== FastText Model Fixer ===")
        
        # 1. Diagnose masalah
        diagnosis = self.diagnose_model()
        
        if diagnosis['recommendation'] == 'model_ok':
            print("✅ Model FastText sudah baik, tidak perlu perbaikan")
            return True
        
        # 2. Backup model lama
        backup_path = self.backup_current_model()
        
        # 3. Buat korpus dari data Al-Quran
        print("📚 Membuat korpus dari data Al-Quran...")
        dataset_dir = os.path.join(self.base_dir, 'dataset/surah')
        preprocessed_verses = process_quran_data(dataset_dir=dataset_dir)
        
        corpus_path = os.path.join(self.base_dir, 'temp_quran_corpus.txt')
        with open(corpus_path, 'w', encoding='utf-8') as f:
            for verse_id, verse_info in preprocessed_verses.items():
                tokens = verse_info['tokens']
                f.write(' '.join(tokens) + '\n')
        
        try:
            # 4. Buat model baru
            new_model_path = self.create_new_fasttext_model(corpus_path)
            
            # 5. Test kompatibilitas
            if self.test_model_compatibility(new_model_path):
                print("✅ Model baru berhasil dibuat dan kompatibel")
                
                # 6. Update sistem
                print("🔄 Mengupdate sistem dengan model baru...")
                from backend.initialize import initialize_fasttext
                initialize_fasttext(preprocessed_verses)
                
                print("✅ Masalah model FastText berhasil diperbaiki!")
                return True
            else:
                print("❌ Model baru masih bermasalah")
                return False
                
        finally:
            # Bersihkan file temporary
            if os.path.exists(corpus_path):
                os.remove(corpus_path)
                print(f"🧹 File temporary dibersihkan: {corpus_path}")
    
    def create_simple_test_model(self):
        """
        Membuat model test sederhana untuk debugging
        """
        print("=== Creating Simple Test Model ===")
        
        # Buat korpus sederhana
        test_sentences = [
            ['allah', 'maha', 'besar'],
            ['nabi', 'muhammad', 'rasul'],
            ['shalat', 'wajib', 'bagi', 'muslim'],
            ['puasa', 'ramadhan', 'bulan', 'suci'],
            ['zakat', 'wajib', 'bagi', 'yang', 'mampu'],
            ['haji', 'wajib', 'bagi', 'yang', 'kuat'],
            ['quran', 'kitab', 'suci', 'islam'],
            ['masjid', 'tempat', 'ibadah'],
            ['doa', 'permohonan', 'kepada', 'allah'],
            ['malaikat', 'makhluk', 'allah']
        ]
        
        from gensim.models.fasttext import FastText
        
        # Buat model test
        model = FastText(
            test_sentences,
            vector_size=200,
            window=5,
            min_count=1,
            min_n=2,
            max_n=5,
            workers=1,
            sg=1,
            epochs=5
        )
        
        # Simpan model test
        test_model_path = os.path.join(self.models_dir, 'fasttext_test.model')
        os.makedirs(self.models_dir, exist_ok=True)
        model.save(test_model_path)
        
        print(f"✅ Model test disimpan di: {test_model_path}")
        print(f"📊 Ukuran vocabulary: {len(model.wv.key_to_index)}")
        
        # Test model
        try:
            test_model = FastText.load(test_model_path)
            vector = test_model.wv['allah']
            print(f"✅ Model test berhasil dimuat dan dapat digunakan")
            return test_model_path
        except Exception as e:
            print(f"❌ Error pada model test: {e}")
            return None

def main():
    """
    Main function untuk memperbaiki model FastText
    """
    print("=== FastText Model Fixer ===")
    
    # Buat fixer
    fixer = FastTextModelFixer()
    
    # Diagnose masalah
    diagnosis = fixer.diagnose_model()
    
    print(f"\n📋 Diagnosis:")
    print(f"  Model ada: {diagnosis['model_exists']}")
    print(f"  Ukuran file: {diagnosis['model_size']} bytes")
    print(f"  Error type: {diagnosis['error_type']}")
    print(f"  Rekomendasi: {diagnosis['recommendation']}")
    
    # Tanya user apakah ingin memperbaiki
    if diagnosis['recommendation'] != 'model_ok':
        print(f"\n🔧 Apakah Anda ingin memperbaiki model? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', 'ya']:
                success = fixer.fix_model_issue()
                if success:
                    print("\n🎉 Model FastText berhasil diperbaiki!")
                    print("🚀 Siap untuk menjalankan eksperimen")
                else:
                    print("\n❌ Gagal memperbaiki model")
            else:
                print("⏭️ Melewati perbaikan model")
        except KeyboardInterrupt:
            print("\n⏹️ Dibatalkan oleh user")
    else:
        print("\n✅ Model sudah baik, tidak perlu perbaikan")

if __name__ == "__main__":
    import time
    main() 