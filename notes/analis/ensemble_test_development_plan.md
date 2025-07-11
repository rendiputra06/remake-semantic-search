# Rencana Pengembangan Halaman Uji & Visualisasi Model Ensemble

## 1. Analisis Fitur Pencarian Semantik: Model Ensemble

### a. Deskripsi Model Ensemble

- Model ensemble menggabungkan tiga model embedding: **Word2Vec**, **FastText**, dan **GloVe**.
- Penggabungan dilakukan dengan dua pendekatan utama:
  - **Weighted Averaging**: Skor dari masing-masing model digabungkan dengan bobot tertentu.
  - **Voting Bonus**: Ayat yang muncul di ≥2 model mendapat bonus skor.
  - **Meta-Ensemble**: Logistic Regression digunakan untuk memprediksi relevansi berdasarkan skor individual dan fitur tambahan (panjang query, panjang ayat, dsb).

### b. Implementasi

- Kode utama: `backend/ensemble_embedding.py` (`EnsembleEmbeddingModel`)
- Meta-ensemble: `backend/meta_ensemble.py`
- Service layer: `app/api/services/search_service.py`
- Endpoint API: `app/api/routes/models.py` (`/search/ensemble`)
- Evaluasi: `app/api/routes/evaluation.py`

### c. Kelebihan

- Robustness, coverage lebih luas, hasil lebih stabil, dan adaptif.
- Bisa dikembangkan lebih lanjut dengan model kontekstual (BERT, dsb).

### d. Keterbatasan

- Komputasi dan memori lebih berat.
- Tuning lebih kompleks.
- Latensi lebih tinggi.

---

## 2. Rencana Pengembangan: Halaman Uji & Visualisasi Ensemble

### A. Tujuan

Membuat halaman baru untuk:

- Menguji hasil model ensemble secara interaktif.
- Mengatur metode ensemble (weighted, meta, voting, dsb).
- Memvisualisasikan proses penggabungan skor antar model.
- Memberikan insight ke user tentang cara kerja ensemble.

### B. Fitur Halaman Uji Ensemble

1. **Input Query**

   - Form untuk memasukkan query pencarian.
   - Pilihan model ensemble (weighted, meta, voting).
   - Pengaturan bobot masing-masing model (slider/input).
   - Opsi threshold dan limit hasil.

2. **Hasil Pencarian**

   - Tabel/list hasil ayat beserta:
     - Skor ensemble.
     - Skor individual (Word2Vec, FastText, GloVe).
     - Indikator voting bonus.
     - Jika meta-ensemble: tampilkan skor prediksi & probabilitas.

3. **Visualisasi Proses Ensemble**

   - Diagram/graph yang menunjukkan:
     - Kontribusi skor dari masing-masing model.
     - Proses averaging/voting/meta-ensemble.
     - Highlight ayat yang mendapat voting bonus.
   - Tooltip/penjelasan interaktif.

4. **Eksperimen Parameter**

   - User dapat mengubah bobot, threshold, metode ensemble secara real-time dan melihat perubahan hasil.

5. **Export & Analisis**
   - Ekspor hasil ke Excel/CSV.
   - Statistik performa (jumlah ayat, distribusi skor, dsb).

### C. Rencana Implementasi

1. **Backend**

   - Endpoint baru (misal: `/api/ensemble/test`) untuk menerima parameter eksperimen dan mengembalikan hasil + data visualisasi.
   - Modifikasi/ekstensi pada `EnsembleEmbeddingModel` untuk expose data intermediate (skor individual, voting, dsb).

2. **Frontend**

   - Halaman baru: `ensemble_test.html` (atau React/Vue jika SPA).
   - Komponen:
     - Form input & kontrol parameter.
     - Tabel hasil.
     - Komponen visualisasi (bar chart, pie, dsb).
   - Integrasi dengan endpoint backend.

3. **Testing**
   - Unit test untuk backend (skor, voting, meta-ensemble).
   - UI/UX test untuk frontend.

---

## 3. Perubahan Navigasi

### A. Menu Tesaurus

- Gabungkan menu "Tesaurus" ke dalam dropdown "Informasi" di header.

### B. Menu Ensemble

- Tambahkan menu baru di header/dropdown untuk mengakses halaman uji model ensemble.

---

## 4. Roadmap Bertahap

1. **Tahap 1: Analisis & Desain**

   - Review kebutuhan user & desain UI/UX halaman uji ensemble.
   - Identifikasi endpoint dan data yang dibutuhkan.

2. **Tahap 2: Backend**

   - Buat endpoint baru untuk eksperimen ensemble.
   - Pastikan data intermediate (skor, voting, dsb) tersedia untuk visualisasi.

3. **Tahap 3: Frontend**

   - Implementasi halaman uji ensemble.
   - Integrasi visualisasi interaktif.

4. **Tahap 4: Integrasi Navigasi**

   - Update menu header sesuai permintaan.

5. **Tahap 5: Testing & Dokumentasi**
   - Uji fungsionalitas dan UX.
   - Dokumentasikan cara penggunaan halaman uji ensemble.

---

## 5. Catatan & Saran Pengembangan Lanjutan

- **Integrasi Model Kontekstual**: Tambahkan BERT/IndoBERT ke ensemble.
- **Dynamic Weighting**: Bobot model bisa otomatis menyesuaikan karakteristik query.
- **Feedback Loop**: User bisa memberi feedback relevansi untuk training meta-ensemble.
- **Analisis Error**: Fitur analisis kasus di mana ensemble gagal/berbeda dengan model individual.
