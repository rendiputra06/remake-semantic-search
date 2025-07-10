# Analisis Model Ensemble

## Deskripsi Umum

Model Ensemble dalam sistem pencarian semantik Al-Quran adalah pendekatan yang menggabungkan kekuatan dari tiga model word embedding dasar: Word2Vec, FastText, dan GloVe. Tujuan utama dari pendekatan ensemble adalah untuk meningkatkan akurasi dan robustness hasil pencarian dengan memanfaatkan kelebihan masing-masing model dan meminimalkan kelemahan individual. Sistem ini mengimplementasikan dua jenis ensemble: weighted averaging (dengan voting bonus) dan meta-ensemble berbasis machine learning.

## Implementasi dalam Sistem

### Struktur Kode

Model Ensemble diimplementasikan dalam file `backend/ensemble_embedding.py` dengan kelas utama `EnsembleEmbeddingModel`. Kelas ini menangani:

1. **Inisialisasi Model Dasar**: Menggunakan instance dari Word2Vec, FastText, dan GloVe
2. **Pembobotan Model**: Menentukan kontribusi relatif dari setiap model
3. **Voting Bonus**: Memberikan bonus untuk ayat yang muncul di beberapa model
4. **Meta-Ensemble**: Menggunakan model machine learning untuk memprediksi relevansi

### Komponen Utama

#### 1. Weighted Averaging

```python
# Fallback to weighted ensemble
weights = []
sims = []
if w2v_sim > 0:
    weights.append(self.word2vec_weight)
    sims.append(w2v_sim)
if ft_sim > 0:
    weights.append(self.fasttext_weight)
    sims.append(ft_sim)
if glove_sim > 0:
    weights.append(self.glove_weight)
    sims.append(glove_sim)
if not sims:
    continue
ensemble_score = sum(w * s for w, s in zip(weights, sims)) / sum(weights)
```

#### 2. Voting Bonus

```python
# Voting: bonus jika ayat muncul di >=2 model
model_count = sum([w2v_sim > 0, ft_sim > 0, glove_sim > 0])
if model_count >= 2:
    ensemble_score += self.voting_bonus
```

#### 3. Meta-Ensemble

```python
# Use meta-ensemble prediction
meta_result = self.meta_ensemble.predict_relevance(
    w2v_sim, ft_sim, glove_sim, query_length, verse_length
)
ensemble_score = meta_result['relevance_score']
```

### Proses Ensemble Query Vector

Untuk query, model ensemble menggunakan rata-rata dari vektor yang dihasilkan oleh ketiga model dasar:

```python
def _calculate_query_vector(self, tokens: List[str]) -> np.ndarray:
    """
    Menghitung vektor query dengan averaging dari ketiga model.
    """
    v1 = self.word2vec_model._calculate_verse_vector(tokens)
    v2 = self.fasttext_model._calculate_verse_vector(tokens)
    v3 = self.glove_model._calculate_verse_vector(tokens)
    # Jika salah satu None, abaikan dari averaging
    vectors = [v for v in [v1, v2, v3] if v is not None]
    if not vectors:
        return None
    return l2_normalize(np.mean(vectors, axis=0))
```

### Proses Pencarian Ensemble

Proses pencarian ensemble melibatkan beberapa langkah:

1. **Pencarian Individual**: Melakukan pencarian dengan setiap model dasar
2. **Penggabungan Hasil**: Mengumpulkan semua ayat unik dari ketiga model
3. **Perhitungan Skor Ensemble**: Menggunakan weighted averaging atau meta-ensemble
4. **Penerapan Voting Bonus**: Memberikan bonus untuk ayat yang muncul di beberapa model
5. **Pengurutan dan Filtering**: Mengurutkan hasil berdasarkan skor ensemble dan menerapkan threshold

## Meta-Ensemble

Meta-Ensemble adalah pendekatan yang lebih canggih yang menggunakan model machine learning (Logistic Regression) untuk memprediksi relevansi ayat berdasarkan skor dari model-model dasar dan fitur tambahan. Implementasi ini terdapat dalam file `backend/meta_ensemble.py`.

### Fitur Meta-Ensemble

```python
def prepare_features(self, 
                    word2vec_score: float, 
                    fasttext_score: float, 
                    glove_score: float,
                    query_length: int = 0,
                    verse_length: int = 0) -> np.ndarray:
    """
    Menyiapkan feature vector untuk meta-ensemble
    """
    features = [
        word2vec_score,
        fasttext_score, 
        glove_score,
        query_length,
        verse_length,
        # Feature tambahan
        word2vec_score * fasttext_score,  # Interaction term
        word2vec_score * glove_score,
        fasttext_score * glove_score,
        np.mean([word2vec_score, fasttext_score, glove_score]),  # Average score
        np.std([word2vec_score, fasttext_score, glove_score]),   # Score variance
        max(word2vec_score, fasttext_score, glove_score),        # Max score
        min(word2vec_score, fasttext_score, glove_score)         # Min score
    ]
    return np.array(features).reshape(1, -1)
```

### Proses Training Meta-Ensemble

Meta-Ensemble dilatih menggunakan data yang berisi skor dari ketiga model dasar dan label relevansi (ground truth). Model menggunakan Logistic Regression untuk mempelajari pola yang menunjukkan relevansi ayat.

## Kelebihan Model Ensemble

1. **Robustness**: Lebih tahan terhadap noise dan outlier dibandingkan model individual
2. **Coverage yang Lebih Luas**: Menggabungkan kelebihan setiap model (Word2Vec untuk frasa umum, FastText untuk kata OOV, GloVe untuk hubungan semantik global)
3. **Kualitas Hasil yang Lebih Baik**: Secara umum memberikan hasil yang lebih relevan dan komprehensif
4. **Adaptabilitas**: Dapat disesuaikan dengan kebutuhan melalui pengaturan bobot model
5. **Pembelajaran dari Data**: Meta-ensemble dapat belajar dari data relevansi untuk meningkatkan performa

## Keterbatasan Model Ensemble

1. **Kompleksitas Komputasi**: Membutuhkan lebih banyak sumber daya komputasi karena harus menjalankan tiga model
2. **Overhead Memori**: Membutuhkan lebih banyak memori untuk menyimpan tiga model sekaligus
3. **Ketergantungan pada Model Dasar**: Kualitas ensemble terbatas oleh kualitas model-model dasarnya
4. **Kompleksitas Tuning**: Membutuhkan tuning yang lebih kompleks (bobot, voting bonus, parameter meta-ensemble)
5. **Overhead Latency**: Waktu respons yang lebih lambat karena harus memproses tiga model

## Performa dalam Sistem

Berdasarkan implementasi dalam kode, model Ensemble menunjukkan karakteristik sebagai berikut:

1. **Weighted Averaging**: Memberikan fleksibilitas untuk menyesuaikan kontribusi setiap model
2. **Voting Mechanism**: Memberikan bonus untuk ayat yang muncul di beberapa model, meningkatkan confidence
3. **Meta-Learning**: Menggunakan machine learning untuk mempelajari pola relevansi yang lebih kompleks
4. **Fallback Mechanism**: Jika meta-ensemble tidak tersedia, sistem akan fallback ke weighted averaging

## Peluang Pengembangan

1. **Peningkatan Model Meta-Ensemble**: Mengganti Logistic Regression dengan model yang lebih canggih (XGBoost, Neural Network)
2. **Ekspansi Fitur**: Menambahkan fitur linguistik dan kontekstual untuk meta-ensemble
3. **Dynamic Weighting**: Mengimplementasikan pembobotan dinamis berdasarkan karakteristik query
4. **Ensemble Diversifikasi**: Menambahkan model-model dengan arsitektur yang lebih beragam
5. **Online Learning**: Mengimplementasikan pembelajaran berkelanjutan dari feedback pengguna

## Rekomendasi Pengembangan Bertahap

### Tahap 1: Optimasi Meta-Ensemble
- Evaluasi performa model meta-ensemble saat ini dengan metrik yang komprehensif
- Eksperimen dengan algoritma machine learning yang lebih canggih (XGBoost, Neural Network)
- Implementasi feature engineering yang lebih canggih

### Tahap 2: Pembobotan Dinamis
- Implementasi sistem pembobotan dinamis berdasarkan karakteristik query
- Pengembangan algoritma untuk mendeteksi tipe query dan menyesuaikan bobot model
- Evaluasi performa dengan pembobotan dinamis vs statis

### Tahap 3: Integrasi Model Kontekstual
- Tambahkan model kontekstual (BERT/IndoBERT) ke dalam ensemble
- Kembangkan strategi untuk mengintegrasikan embedding kontekstual dengan non-kontekstual
- Evaluasi kontribusi model kontekstual terhadap performa ensemble

## Kesimpulan

Model Ensemble dalam sistem pencarian semantik Al-Quran menyediakan pendekatan yang komprehensif dan robust dengan menggabungkan kekuatan dari tiga model word embedding yang berbeda. Penggunaan weighted averaging dengan voting bonus dan meta-ensemble berbasis machine learning menunjukkan pendekatan yang sophisticated untuk mengoptimalkan hasil pencarian.

Meskipun membutuhkan lebih banyak sumber daya komputasi, trade-off ini sebanding dengan peningkatan kualitas hasil pencarian. Pengembangan lebih lanjut pada meta-ensemble dan implementasi pembobotan dinamis berpotensi meningkatkan performa sistem secara signifikan. Integrasi dengan model kontekstual modern seperti BERT juga merupakan arah pengembangan yang menjanjikan untuk masa depan. 