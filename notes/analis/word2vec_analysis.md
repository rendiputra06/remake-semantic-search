# Analisis Model Word2Vec

## Deskripsi Umum

Word2Vec adalah model word embedding yang dikembangkan oleh Google pada tahun 2013. Model ini menggunakan jaringan saraf dangkal untuk mempelajari representasi vektor dari kata-kata berdasarkan konteks kemunculannya dalam korpus teks. Dalam sistem pencarian semantik Al-Quran ini, Word2Vec digunakan sebagai salah satu model dasar untuk menghasilkan representasi vektor dari ayat-ayat Al-Quran.

## Implementasi dalam Sistem

### Konfigurasi Model

- **Path Model**: `models/idwiki_word2vec/idwiki_word2vec_200_new_lower.model`
- **Dimensi Vektor**: 200
- **Sumber Korpus**: Wikipedia Indonesia (berdasarkan nama file)
- **Format Model**: Gensim KeyedVectors/Word2Vec

### Struktur Kode

Model Word2Vec diimplementasikan dalam file `backend/word2vec_model.py` dengan kelas utama `Word2VecModel`. Kelas ini menangani:

1. **Pemuatan Model**: Melalui metode `load_model()`
2. **Pembuatan Vektor Ayat**: Melalui metode `create_verse_vectors()`
3. **Pencarian Semantik**: Melalui metode `search()`
4. **Penyimpanan & Pemuatan Vektor**: Melalui metode `save_verse_vectors()` dan `load_verse_vectors()`

### Proses Embedding Ayat

Proses mengubah ayat menjadi vektor dilakukan dengan langkah-langkah berikut:

1. **Preprocessing**: Tokenisasi, penghapusan stopwords, dan normalisasi teks
2. **Ekstraksi Vektor Kata**: Setiap token (kata) diubah menjadi vektor menggunakan model Word2Vec
3. **Agregasi Vektor**: Vektor-vektor kata dirata-ratakan (mean pooling) untuk mendapatkan vektor ayat
4. **Normalisasi**: Vektor hasil rata-rata dinormalisasi dengan L2-normalization

```python
def _calculate_verse_vector(self, tokens: List[str]) -> np.ndarray:
    if not tokens:
        return None
    
    token_vectors = []
    for token in tokens:
        try:
            if hasattr(self.model, 'key_to_index') and token in self.model.key_to_index:
                token_vectors.append(self.model[token])
            elif hasattr(self.model, 'wv'):
                if token in self.model.wv:
                    token_vectors.append(self.model.wv[token])
            else:
                try:
                    vector = self.model[token]
                    token_vectors.append(vector)
                except:
                    pass
        except Exception as e:
            print(f"Error getting vector for token '{token}': {e}")
            continue
    
    if not token_vectors:
        return None
    
    verse_vector = np.mean(token_vectors, axis=0)
    return l2_normalize(verse_vector)
```

### Proses Pencarian

Pencarian semantik menggunakan Word2Vec dilakukan dengan langkah-langkah berikut:

1. **Preprocessing Query**: Query pengguna diproses dengan cara yang sama seperti ayat
2. **Embedding Query**: Query diubah menjadi vektor menggunakan proses yang sama dengan ayat
3. **Perhitungan Kesamaan**: Cosine similarity dihitung antara vektor query dan vektor setiap ayat
4. **Pengurutan Hasil**: Hasil diurutkan berdasarkan nilai similarity (dari tinggi ke rendah)
5. **Filtering**: Hasil dengan similarity di bawah threshold dibuang
6. **Formatting**: Hasil diformat dengan informasi ayat yang relevan

## Kelebihan Model Word2Vec

1. **Efisiensi Komputasi**: Model Word2Vec relatif ringan dan cepat dibandingkan model kontekstual seperti BERT
2. **Representasi Semantik Dasar**: Mampu menangkap hubungan semantik dasar antar kata
3. **Kebutuhan Memori Rendah**: Membutuhkan memori yang lebih sedikit dibandingkan model yang lebih kompleks
4. **Kecepatan Inferensi**: Proses embedding dan pencarian relatif cepat

## Keterbatasan Model Word2Vec

1. **Tidak Menangani Kata OOV (Out-of-Vocabulary)**: Tidak dapat menghasilkan vektor untuk kata yang tidak ada dalam vocabulary
2. **Tidak Sensitif Konteks**: Setiap kata memiliki satu vektor tetap, tidak berubah berdasarkan konteks penggunaannya
3. **Tidak Menangkap Morfologi**: Tidak memahami struktur morfologi kata (berbeda dengan FastText)
4. **Keterbatasan pada Frasa**: Kurang optimal untuk menangkap makna frasa yang kompleks
5. **Ketergantungan pada Kualitas Korpus**: Performa sangat bergantung pada kualitas dan ukuran korpus pelatihan

## Performa dalam Sistem

Berdasarkan analisis kode, model Word2Vec menunjukkan performa sebagai berikut:

1. **Kecepatan**: Paling cepat di antara ketiga model (Word2Vec, FastText, GloVe)
2. **Cakupan Hasil**: Lebih sedikit hasil dibandingkan FastText (karena keterbatasan vocabulary)
3. **Kualitas Semantik**: Baik untuk frasa dan idiom umum, namun kurang optimal untuk kata-kata jarang

## Peluang Pengembangan

1. **Peningkatan Metode Agregasi**: Mengganti mean pooling dengan metode yang lebih canggih seperti weighted pooling atau SIF (Smooth Inverse Frequency)
2. **Fine-tuning Khusus Domain**: Melakukan fine-tuning model pada korpus terjemahan Al-Quran untuk meningkatkan relevansi
3. **Hybrid dengan Model Kontekstual**: Mengkombinasikan dengan model kontekstual untuk meningkatkan kualitas embedding
4. **Optimasi Parameter**: Eksperimen dengan parameter seperti window size, dimensi vektor, dan algoritma training
5. **Eksplorasi Arsitektur Alternatif**: Mengevaluasi variasi Word2Vec seperti Skip-gram vs CBOW untuk kasus penggunaan spesifik

## Rekomendasi Pengembangan Bertahap

### Tahap 1: Optimasi Metode Agregasi
- Implementasi weighted pooling berdasarkan TF-IDF
- Implementasi SIF (Smooth Inverse Frequency)
- Evaluasi perbandingan performa dengan metode agregasi yang berbeda

### Tahap 2: Domain Adaptation
- Kumpulkan korpus terjemahan Al-Quran dan literatur Islam dalam bahasa Indonesia
- Fine-tuning model Word2Vec pada korpus domain-specific
- Evaluasi peningkatan performa pada tugas pencarian semantik Al-Quran

### Tahap 3: Integrasi dengan Fitur Linguistik
- Tambahkan fitur linguistik seperti POS tagging dalam proses embedding
- Implementasi pembobotan kata berdasarkan kepentingan semantik
- Evaluasi kontribusi fitur linguistik terhadap kualitas hasil

## Kesimpulan

Model Word2Vec memberikan fondasi yang solid untuk sistem pencarian semantik Al-Quran dengan keseimbangan yang baik antara performa dan efisiensi. Meskipun memiliki keterbatasan dibandingkan model yang lebih modern, Word2Vec tetap menjadi pilihan yang layak untuk sistem yang membutuhkan respons cepat dan sumber daya komputasi yang terbatas.

Pengembangan lebih lanjut dapat difokuskan pada peningkatan metode agregasi dan domain adaptation untuk meningkatkan relevansi hasil tanpa mengorbankan efisiensi yang menjadi kekuatan utama model ini. 