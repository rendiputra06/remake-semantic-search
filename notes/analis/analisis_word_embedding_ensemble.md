# Analisis Model Word Embedding & Ensemble

## Ringkasan Implementasi Saat Ini

### Word2Vec, FastText, GloVe

- **Vektor ayat** dihitung sebagai rata-rata vektor kata (mean pooling).
- **Similarity**: cosine similarity antara vektor query dan vektor ayat.
- **Filtering**: hanya ayat dengan similarity >= threshold yang diambil.
- **Sorting**: hasil diurutkan dari similarity tertinggi.
- **Limit**: ambil N teratas sesuai limit.

### EnsembleEmbeddingModel

- **Averaging**: vektor ayat ensemble = rata-rata vektor dari ketiga model (Word2Vec, FastText, GloVe).
- **Query vector**: juga rata-rata dari ketiga model.
- **Hasil**:
  - Ambil hasil dari masing-masing model (limit\*3, threshold).
  - Gabungkan semua verse_id unik.
  - Skor individual diambil dari masing-masing model (0 jika tidak ada).
  - Skor ensemble = rata-rata dari skor individual yang > 0.
  - Hanya ayat dengan skor ensemble >= threshold yang diambil.
  - Hasil diurutkan dan diambil limit teratas.

## Kelebihan

- Sederhana dan mudah dipahami.
- Averaging cukup efektif untuk baseline.
- Cosine similarity adalah standar untuk vektor embedding.

## Potensi Peningkatan

1. **Pooling Lebih Canggih**

   - Mean pooling bisa diganti/ditambah dengan max pooling, attention pooling, atau weighted pooling (misal, bobot IDF untuk kata penting).

2. **Normalisasi Vektor**

   - Pastikan semua vektor sudah dinormalisasi (unit norm) sebelum similarity, agar cosine similarity benar-benar valid.

3. **Strategi Ensemble**

   - Saat ini, ensemble hanya averaging skor similarity. Bisa ditingkatkan:
     - Weighted ensemble: Bobot model bisa diatur (misal, Word2Vec lebih tinggi jika terbukti lebih akurat).
     - Voting: Jika dua model setuju, lebih diprioritaskan.
     - Meta-ensemble: Gunakan model ML sederhana (misal logistic regression) untuk menggabungkan skor model.

4. **Threshold Adaptif**

   - Threshold bisa dibuat adaptif tergantung query atau distribusi similarity (misal, ambil top-N percentile).

5. **Recall Lebih Luas**

   - Untuk query pendek, limit hasil dari masing-masing model bisa diperbesar sebelum ensemble, agar recall lebih baik.

6. **Handling OOV (Out-of-Vocabulary)**

   - FastText sudah bagus untuk OOV, tapi Word2Vec/GloVe tidak. Bisa tambahkan fallback: jika query tidak ada di model, gunakan model lain.

7. **Explainability**

   - Tampilkan skor individual model di UI (sudah ada, bagus).

8. **Optimasi Performa**
   - Untuk dataset besar, similarity bisa dihitung dengan batch/matrix multiplication (lebih cepat).

## Kesimpulan & Saran

- Arsitektur saat ini sudah baik untuk baseline dan mudah dikembangkan.
- Peningkatan utama:
  - Coba weighted ensemble (misal, bobot berdasarkan hasil evaluasi).
  - Eksperimen pooling lain (max, attention, IDF-weighted).
  - Pastikan normalisasi vektor konsisten.
  - Threshold adaptif untuk hasil lebih relevan.
- Jika ingin lebih advance: pertimbangkan fine-tuning embedding atau gunakan model transformer (misal, SBERT) untuk masa depan.
