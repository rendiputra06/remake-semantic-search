# Task List: Penggabungan Word2Vec, FastText, dan GloVe untuk Mesin Pencarian Semantik

## Latar Belakang

Saat ini, sistem pencarian semantik mendukung tiga model embedding: Word2Vec, FastText, dan GloVe. Namun, hanya satu model yang digunakan per pencarian. Penggabungan (ensemble) ketiga model diharapkan dapat meningkatkan kualitas dan robustnes hasil pencarian.

## Rencana Pengembangan

1. **Analisis & Desain**

   - Analisis pipeline pencarian semantik dan interface model embedding.
   - Rancang arsitektur ensemble yang fleksibel (averaging, voting, weighted).
   - Tentukan interface baru, misal: `EnsembleEmbeddingModel`.

2. **Implementasi**

   - Buat modul/kelas ensemble yang menginisialisasi dan mengelola ketiga model embedding.
   - Implementasikan metode penggabungan vektor dan/atau hasil pencarian.
   - Tambahkan opsi ensemble pada API dan UI (opsional).

3. **Integrasi & Refaktor**

   - Integrasikan ensemble ke pipeline pencarian.
   - Refaktor endpoint API agar mendukung mode ensemble.

4. **Testing & Evaluasi**

   - Buat unit test dan evaluasi kualitas hasil pencarian (precision, recall, relevansi).
   - Lakukan benchmarking terhadap mode individual vs ensemble.

5. **Dokumentasi & Deployment**
   - Update dokumentasi teknis dan user guide.
   - Siapkan script migrasi/inisialisasi jika diperlukan.

---

## Task List

### 1. Analisis & Desain

- [x] Review pipeline pencarian semantik dan interface model embedding.
- [x] Rancang interface/abstraksi untuk ensemble model.
- [x] Pilih metode ensemble utama (averaging, voting, weighted).

### 2. Implementasi Ensemble

- [x] Buat kelas `EnsembleEmbeddingModel` di backend.
- [x] Implementasikan inisialisasi paralel untuk ketiga model.
- [x] Implementasikan metode penggabungan vektor (concatenate/average).
- [x] Implementasikan metode penggabungan hasil pencarian (voting/ranking).

### 3. Integrasi API

- [x] Tambahkan opsi `ensemble` pada endpoint pencarian.
- [x] Update endpoint `/models` untuk menampilkan opsi ensemble.
- [x] Pastikan pipeline pencarian bisa memilih mode ensemble.
  - Integrasi sudah dilakukan di `app/api/routes/search.py` dan `app/api/services/search_service.py`.

### 4. Testing & Evaluasi

- [x] Buat unit test untuk ensemble model.
- [x] Lakukan evaluasi kualitas hasil pencarian (bandingkan dengan model individual).
- [x] Benchmark performa dan respons API.

### 5. Dokumentasi

- [ ] Update dokumentasi teknis (README, docstring, API docs).
- [ ] Tambahkan panduan penggunaan mode ensemble untuk user/admin.

### 6. Deployment & Maintenance

- [ ] Uji integrasi di staging/dev.
- [ ] Deploy ke production setelah lulus QA.
- [ ] Monitor performa dan feedback user.
