# Analisis Model GloVe

## Deskripsi Umum

GloVe (Global Vectors for Word Representation) adalah model word embedding yang dikembangkan oleh Stanford NLP Group. Berbeda dengan Word2Vec yang berfokus pada konteks lokal kata, GloVe menggabungkan informasi statistik global (co-occurrence matrix) dengan konteks lokal. Pendekatan ini memungkinkan GloVe untuk menangkap hubungan semantik dan sintaksis yang lebih kaya. Dalam sistem pencarian semantik Al-Quran ini, GloVe digunakan sebagai salah satu model untuk menghasilkan representasi vektor dari ayat-ayat Al-Quran.

## Implementasi dalam Sistem

### Konfigurasi Model

- **Path Model**: `models/glove/alquran_vectors.txt`
- **Format Model**: Word2Vec-compatible text format
- **Dimensi Vektor**: Tidak disebutkan secara eksplisit dalam kode
- **Sumber Korpus**: Berdasarkan nama file, kemungkinan dilatih pada korpus Al-Quran

### Struktur Kode

Model GloVe diimplementasikan dalam file `backend/glove_model.py` dengan kelas utama `GloVeModel`. Kelas ini menangani:

1. **Pemuatan Model**: Melalui metode `load_model()`
2. **Pembuatan Vektor Ayat**: Melalui metode `create_verse_vectors()`
3. **Pencarian Semantik**: Melalui metode `search()`
4. **Penyimpanan & Pemuatan Vektor**: Melalui metode `save_verse_vectors()` dan `load_verse_vectors()`

### Proses Embedding Ayat

Proses mengubah ayat menjadi vektor dilakukan dengan langkah-langkah berikut:

1. **Preprocessing**: Tokenisasi, penghapusan stopwords, dan normalisasi teks
2. **Ekstraksi Vektor Kata**: Setiap token (kata) diubah menjadi vektor menggunakan model GloVe
3. **Agregasi Vektor**: Vektor-vektor kata dirata-ratakan (mean pooling) untuk mendapatkan vektor ayat
4. **Normalisasi**: Vektor hasil rata-rata dinormalisasi dengan L2-normalization

```python
def _calculate_verse_vector(self, tokens: List[str]) -> np.ndarray:
    """
    Menghitung vektor untuk sebuah ayat berdasarkan token-tokennya
    """
    if not tokens:
        return None
    
    # Kumpulkan vektor untuk setiap kata
    token_vectors = []
    for token in tokens:
        try:
            if token in self.model:
                vector = self.model[token]
                token_vectors.append(vector)
        except Exception as e:
            print(f"Error getting vector for token '{token}': {e}")
            continue
    
    # Jika tidak ada kata yang ditemukan dalam model, kembalikan None
    if not token_vectors:
        return None
    
    # Hitung rata-rata vektor
    verse_vector = np.mean(token_vectors, axis=0)
    return l2_normalize(verse_vector)
```

### Proses Pencarian

Pencarian semantik menggunakan GloVe dilakukan dengan langkah-langkah yang sama seperti model lainnya:

1. **Preprocessing Query**: Query pengguna diproses dengan cara yang sama seperti ayat
2. **Embedding Query**: Query diubah menjadi vektor menggunakan proses yang sama dengan ayat
3. **Perhitungan Kesamaan**: Cosine similarity dihitung antara vektor query dan vektor setiap ayat
4. **Pengurutan Hasil**: Hasil diurutkan berdasarkan nilai similarity (dari tinggi ke rendah)
5. **Filtering**: Hasil dengan similarity di bawah threshold dibuang
6. **Formatting**: Hasil diformat dengan informasi ayat yang relevan

## Kelebihan Model GloVe

1. **Kombinasi Informasi Global dan Lokal**: Menggabungkan statistik co-occurrence global dengan konteks lokal
2. **Representasi Semantik Kaya**: Mampu menangkap hubungan semantik yang lebih kompleks
3. **Performa pada Analogi**: Unggul dalam tugas analogi semantik dan sintaksis
4. **Efisiensi Training**: Lebih efisien dalam pelatihan dibandingkan Word2Vec untuk korpus besar
5. **Stabilitas Representasi**: Menghasilkan representasi yang lebih stabil karena mempertimbangkan statistik global

## Keterbatasan Model GloVe

1. **Tidak Menangani Kata OOV**: Seperti Word2Vec, tidak dapat menghasilkan vektor untuk kata yang tidak ada dalam vocabulary
2. **Tidak Sensitif Konteks**: Setiap kata memiliki satu vektor tetap, tidak berubah berdasarkan konteks
3. **Membutuhkan Korpus Besar**: Performa optimal membutuhkan korpus yang cukup besar
4. **Keterbatasan pada Frasa**: Kurang optimal untuk menangkap makna frasa yang kompleks
5. **Tidak Menangkap Morfologi**: Tidak memahami struktur morfologi kata (berbeda dengan FastText)

## Performa dalam Sistem

Berdasarkan implementasi dalam kode, model GloVe menunjukkan karakteristik sebagai berikut:

1. **Spesialisasi Domain**: Model GloVe yang digunakan tampaknya dilatih khusus pada korpus Al-Quran (`alquran_vectors.txt`), yang berpotensi memberikan representasi yang lebih relevan untuk domain ini
2. **Integrasi dengan Ensemble**: Digunakan sebagai salah satu komponen dalam model ensemble, berkontribusi pada hasil pencarian yang lebih komprehensif
3. **Implementasi Standar**: Menggunakan pendekatan standar untuk sentence embedding (mean pooling) dan pencarian (cosine similarity)

## Peluang Pengembangan

1. **Peningkatan Metode Agregasi**: Mengganti mean pooling dengan metode yang lebih canggih seperti weighted pooling atau SIF
2. **Ekspansi Korpus Training**: Memperluas korpus training dengan terjemahan Al-Quran dari berbagai sumber dan tafsir
3. **Hybrid dengan Model Kontekstual**: Mengkombinasikan dengan model kontekstual untuk meningkatkan kualitas embedding
4. **Eksplorasi Dimensi Vektor**: Eksperimen dengan berbagai dimensi vektor untuk menemukan trade-off optimal antara kualitas dan efisiensi
5. **Integrasi dengan Knowledge Graph**: Menggabungkan representasi GloVe dengan knowledge graph untuk memperkaya semantik

## Rekomendasi Pengembangan Bertahap

### Tahap 1: Evaluasi dan Optimasi Model yang Ada
- Evaluasi performa model GloVe saat ini dengan metrik yang komprehensif
- Analisis coverage vocabulary terhadap domain Al-Quran
- Identifikasi kasus-kasus di mana model GloVe memberikan hasil terbaik dibandingkan model lain

### Tahap 2: Peningkatan Metode Agregasi
- Implementasi SIF (Smooth Inverse Frequency) untuk pembobotan kata berdasarkan frekuensi
- Implementasi weighted pooling berdasarkan TF-IDF atau metode pembobotan lainnya
- Evaluasi perbandingan performa dengan metode agregasi yang berbeda

### Tahap 3: Pelatihan Model Domain-Specific
- Kumpulkan korpus terjemahan Al-Quran dan literatur Islam yang lebih komprehensif
- Latih model GloVe baru dengan parameter optimal
- Evaluasi peningkatan performa dibandingkan dengan model saat ini

## Kesimpulan

Model GloVe dalam sistem pencarian semantik Al-Quran memberikan dimensi tambahan dengan kemampuannya menangkap hubungan semantik berdasarkan statistik global. Penggunaan model yang tampaknya sudah dilatih khusus untuk domain Al-Quran (`alquran_vectors.txt`) merupakan kekuatan tersendiri yang berpotensi memberikan hasil yang lebih relevan untuk pencarian ayat-ayat Al-Quran.

Pengembangan lebih lanjut dapat difokuskan pada peningkatan metode agregasi untuk menghasilkan representasi ayat yang lebih baik, serta evaluasi dan optimasi model yang sudah ada. Dengan pendekatan bertahap, model GloVe dapat dioptimalkan untuk memberikan kontribusi yang lebih signifikan dalam ensemble model pencarian semantik Al-Quran. 