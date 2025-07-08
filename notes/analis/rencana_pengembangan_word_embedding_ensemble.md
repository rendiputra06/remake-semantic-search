# Rencana Pengembangan Model Word Embedding & Ensemble

## Overview

Rencana pengembangan berdasarkan analisis performa dan potensi peningkatan model word embedding ensemble untuk sistem pencarian semantik Al-Quran.

## Fase Pengembangan

### Fase 1: Optimasi Dasar (Prioritas Tinggi - 2-3 minggu)

#### 1.1 Normalisasi Vektor

- **Tujuan**: Memastikan cosine similarity valid dan konsisten
- **Implementasi**:
  - Tambahkan normalisasi L2 pada semua vektor sebelum similarity calculation
  - Update `backend/ensemble_embedding.py` dan service layer
- **Expected Impact**: Peningkatan akurasi 5-10%
- **Effort**: 2-3 hari

#### 1.2 Threshold Adaptif

- **Tujuan**: Threshold yang lebih cerdas berdasarkan distribusi similarity
- **Implementasi**:
  - Buat fungsi `calculate_adaptive_threshold()` yang menggunakan percentile
  - Threshold = 75th percentile dari similarity scores
  - Fallback ke threshold manual jika distribusi tidak normal
- **Expected Impact**: Recall lebih baik tanpa mengorbankan precision
- **Effort**: 3-4 hari

#### 1.3 Handling OOV (Out-of-Vocabulary)

- **Tujuan**: Menangani kata yang tidak ada di vocabulary
- **Implementasi**:
  - Deteksi OOV words di query
  - Fallback strategy: Word2Vec → FastText → GloVe
  - Untuk kata yang tidak ada di semua model, gunakan zero vector
- **Expected Impact**: Robustness untuk query dengan kata baru
- **Effort**: 2-3 hari

### Fase 2: Peningkatan Ensemble (Prioritas Menengah - 3-4 minggu)

#### 2.1 Weighted Ensemble

- **Tujuan**: Model dengan performa lebih baik diberi bobot lebih tinggi
- **Implementasi**:
  - Tambahkan parameter bobot per model di settings
  - Bobot default berdasarkan hasil evaluasi terakhir
  - Formula: `weighted_score = Σ(weight_i * score_i) / Σ(weight_i)`
- **Expected Impact**: Peningkatan F1-score 10-15%
- **Effort**: 1 minggu

#### 2.2 Voting Mechanism

- **Tujuan**: Menggunakan konsensus antar model
- **Implementasi**:
  - Majority voting: ayat yang muncul di ≥2 model mendapat boost
  - Confidence voting: bobot berdasarkan similarity score
  - Hybrid: kombinasi voting + weighted ensemble
- **Expected Impact**: Precision lebih tinggi untuk ayat yang disepakati model
- **Effort**: 1-2 minggu

#### 2.3 Meta-Ensemble dengan ML

- **Tujuan**: Model ML sederhana untuk menggabungkan skor
- **Implementasi**:
  - Logistic Regression untuk menggabungkan skor individual
  - Training data dari hasil evaluasi sebelumnya
  - Feature: similarity scores dari 3 model + query length + ayat length
- **Expected Impact**: Peningkatan akurasi 15-20%
- **Effort**: 2-3 minggu

### Fase 3: Advanced Pooling (Prioritas Rendah - 2-3 minggu)

#### 3.1 Max Pooling

- **Tujuan**: Menangkap kata-kata yang sangat relevan
- **Implementasi**:
  - Tambahkan opsi pooling method di settings
  - Max pooling: ambil nilai maksimum dari similarity kata-kata
  - Hybrid: kombinasi mean + max pooling
- **Expected Impact**: Sensitivitas lebih tinggi untuk kata kunci
- **Effort**: 1 minggu

#### 3.2 IDF-Weighted Pooling

- **Tujuan**: Memberikan bobot lebih pada kata yang lebih informatif
- **Implementasi**:
  - Hitung IDF untuk setiap kata dalam dataset
  - Weighted mean: `Σ(IDF_i * similarity_i) / Σ(IDF_i)`
  - Cache IDF values untuk performa
- **Expected Impact**: Peningkatan relevansi hasil
- **Effort**: 1-2 minggu

#### 3.3 Attention Pooling

- **Tujuan**: Fokus pada kata-kata yang paling relevan dengan query
- **Implementasi**:
  - Simple attention: bobot berdasarkan similarity dengan query
  - Self-attention: interaksi antar kata dalam ayat
  - Lightweight implementation untuk performa
- **Expected Impact**: Akurasi lebih tinggi untuk query kompleks
- **Effort**: 2-3 minggu

### Fase 4: Optimasi Performa (Ongoing)

#### 4.1 Batch Processing

- **Tujuan**: Percepatan perhitungan similarity
- **Implementasi**:
  - Matrix multiplication untuk batch similarity
  - Vectorization dengan NumPy
  - Parallel processing untuk multiple queries
- **Expected Impact**: 3-5x faster computation
- **Effort**: 1-2 minggu

#### 4.2 Caching Strategy

- **Tujuan**: Mengurangi recomputation
- **Implementasi**:
  - Cache vektor ayat yang sering diakses
  - Cache similarity scores untuk query yang sama
  - LRU cache dengan TTL
- **Expected Impact**: Response time lebih cepat
- **Effort**: 1 minggu

## Timeline Implementasi

```
Minggu 1-2:   Fase 1 (Normalisasi, Threshold Adaptif, OOV)
Minggu 3-6:   Fase 2 (Weighted Ensemble, Voting, Meta-Ensemble)
Minggu 7-9:   Fase 3 (Advanced Pooling)
Minggu 10+:   Fase 4 (Optimasi Performa) + Testing & Tuning
```

## Metrik Evaluasi

### Kuantitatif

- **F1-Score**: Target peningkatan 20-30%
- **Precision**: Target peningkatan 15-25%
- **Recall**: Target peningkatan 10-20%
- **Response Time**: Target < 2 detik untuk query kompleks

### Kualitatif

- **User Experience**: Feedback dari pengguna
- **Robustness**: Handling edge cases
- **Maintainability**: Code quality dan dokumentasi

## Risiko dan Mitigasi

### Risiko Teknis

- **Overfitting**: Gunakan cross-validation dan test set terpisah
- **Performance Degradation**: Monitor response time dan optimize
- **Complexity**: Implementasi bertahap dengan testing di setiap fase

### Risiko Proyek

- **Timeline**: Buffer 20% untuk setiap fase
- **Resources**: Prioritas berdasarkan impact/effort ratio
- **Dependencies**: Identifikasi dan manage dependencies antar fase

## Success Criteria

### Short-term (Fase 1-2)

- F1-score meningkat 10-15%
- Response time tetap < 3 detik
- Zero regression pada existing functionality

### Medium-term (Fase 3)

- F1-score meningkat 20-25%
- Robust handling untuk berbagai jenis query
- User satisfaction score > 4.0/5.0

### Long-term (Fase 4)

- F1-score meningkat 25-30%
- Response time < 2 detik
- Scalable untuk dataset 10x lebih besar

## Monitoring & Evaluation

### Metrics Dashboard

- Real-time monitoring F1-score, precision, recall
- Response time tracking
- Error rate monitoring
- User feedback collection

### A/B Testing

- Compare old vs new implementation
- Gradual rollout untuk user groups
- Statistical significance testing

### Continuous Improvement

- Regular model retraining dengan data baru
- Hyperparameter tuning
- Feature engineering berdasarkan user feedback

## Kesimpulan

Rencana pengembangan ini dirancang untuk meningkatkan performa model secara bertahap dengan risiko minimal. Fokus pada Fase 1 dan 2 akan memberikan impact terbesar dengan effort yang reasonable. Implementasi bertahap memungkinkan testing dan validation di setiap langkah, memastikan kualitas dan stabilitas sistem.
