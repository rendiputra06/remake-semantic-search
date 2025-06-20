# Rencana Improvisasi Fitur Ekspor untuk Analisis Model Semantik

## 1. Latar Belakang dan Tujuan

Saat ini, fitur pencarian semantik mendukung beberapa model (Word2Vec, FastText, GloVe, Ensemble). Fitur ekspor ke Excel sudah ada, namun informasinya masih dasar. Untuk keperluan analisis, evaluasi, dan perbandingan model yang lebih mendalam, kita perlu memperkaya data yang disajikan dalam file Excel tersebut.

**Tujuan Utama:** Meningkatkan fungsionalitas ekspor hasil pencarian semantik agar dapat menyajikan data yang lebih kaya dan mendetail, yang memungkinkan analisis perbandingan yang efektif antara berbagai model.

---

## 2. Analisis Masalah

Keterbatasan utama pada fitur ekspor saat ini adalah:

- **Kurangnya Detail pada Model Ensemble:** Hanya menampilkan skor akhir (rata-rata), tanpa menunjukkan kontribusi skor dari masing-masing model pembentuknya.
- **Informasi Kontekstual yang Minim:** Tidak ada metadata tentang performa (misalnya, durasi pencarian) atau parameter spesifik yang digunakan saat pencarian.
- **Struktur Data yang Bisa Dioptimalkan:** Seluruh informasi disajikan dalam satu sheet, yang bisa menjadi kurang terstruktur saat data semakin kompleks.

---

## 3. Rencana Improvisasi dan Perubahan

Untuk mengatasi keterbatasan di atas, berikut adalah perubahan yang diusulkan:

### 3.1. Penambahan Kolom Data pada Sheet Hasil Utama (`Hasil Pencarian`)

Sheet utama akan diperkaya dengan kolom-kolom berikut:

- **`Peringkat`**: Nomor urut hasil pencarian (1, 2, 3, ...).
- **`Skor Word2Vec`**: (Khusus Ensemble) Skor kemiripan dari model Word2Vec.
- **`Skor FastText`**: (Khusus Ensemble) Skor kemiripan dari model FastText.
- **`Skor GloVe`**: (Khusus Ensemble) Skor kemiripan dari model GloVe.
- **`Skor Rata-rata (Ensemble)`**: Menggantikan kolom `Skor Kesamaan` yang ada saat ini agar lebih jelas.

### 3.2. Penambahan Informasi pada Sheet `Informasi Pencarian`

Sheet ini akan ditambahkan baris baru untuk metadata eksekusi:

- **`Model yang Digunakan`**: Nama model yang dipilih (e.g., `ensemble`).
- **`Durasi Pencarian (detik)`**: Waktu yang dibutuhkan server untuk memproses permintaan pencarian.
- **`Threshold Kesamaan`**: Nilai ambang batas yang digunakan untuk filter hasil.
- **`Jumlah Hasil Awal`**: Jumlah hasil yang ditemukan sebelum dibatasi oleh `limit`.

### 3.3. Struktur Respons API yang Diperlukan

Untuk mewujudkan hal di atas, respons dari API pencarian semantik (`/api/search/search`) perlu dimodifikasi. Contoh struktur data untuk satu hasil pada model `ensemble`:

```json
{
  "surah_number": 2,
  "ayat_number": 3,
  "arabic": "...",
  "translation": "...",
  "similarity": 0.85, // Skor rata-rata
  "individual_scores": {
    "word2vec": 0.88,
    "fasttext": 0.82,
    "glove": 0.85
  }
}
```

Dan respons API secara keseluruhan:

```json
{
  "success": true,
  "data": {
    "query": "iman kepada yang ghaib",
    "model": "ensemble",
    "execution_time": 1.25,
    "threshold": 0.5,
    "results": [...]
  }
}
```

---

## 4. Daftar Tugas (Task List)

Berikut adalah langkah-langkah implementasi yang perlu dilakukan:

### Tahap 1: Backend - Modifikasi API Pencarian (`/api/search/search`)

- **File Target:** `app/api/services/search_service.py` (atau di mana logika pemanggilan model berada) dan `app/api/routes/search.py`.
- **Tugas:**
  1.  **Ukur Durasi Eksekusi:** Implementasikan mekanisme untuk mengukur waktu (dalam detik) dari awal hingga akhir proses pencarian di sisi server.
  2.  **Modifikasi Logika Ensemble:** Ubah fungsi pencarian `ensemble` agar tidak hanya mengembalikan skor rata-rata (`mean`), tetapi juga skor individual dari setiap model (Word2Vec, FastText, GloVe).
  3.  **Perbarui Struktur Respons:** Sesuaikan endpoint API di `app/api/routes/search.py` untuk mengemas `execution_time`, `threshold`, dan `individual_scores` (jika ada) ke dalam JSON respons yang dikirim ke frontend.

### Tahap 2: Backend - Modifikasi API Ekspor (`/api/export/excel`)

- **File Target:** `app/api/routes/export.py`.
- **Tugas:**
  1.  **Baca Data Baru:** Modifikasi fungsi `export_excel` untuk membaca `individual_scores`, `execution_time`, dan metadata lainnya dari `data_json` yang dikirim oleh frontend.
  2.  **Tambahkan Kolom Baru:** Saat membuat DataFrame Pandas, tambahkan kolom `Peringkat`, `Skor Word2Vec`, `Skor FastText`, dan `Skor GloVe`. Pastikan untuk menangani kasus jika data ini tidak ada (misalnya, untuk pencarian non-ensemble) agar tidak terjadi error.
  3.  **Perbarui Sheet Informasi:** Tambahkan baris baru ke `info_df` untuk menampilkan `Durasi Pencarian` dan `Threshold Kesamaan`.

### Tahap 3: Frontend - Verifikasi (Tidak Ada Perubahan Kode)

- **File Target:** `templates/index.html`.
- **Tugas:**
  1.  **Verifikasi Pengiriman Data:** Pastikan bahwa JavaScript yang ada (`exportToExcel`) sudah secara otomatis mengirimkan seluruh data hasil pencarian yang baru (yang sudah diperkaya oleh Tahap 1) ke API ekspor. Seharusnya tidak diperlukan perubahan, karena ia mengirim `window.searchResults` secara keseluruhan. Cukup diverifikasi.

### Tahap 4: Pengujian Menyeluruh

- **Tugas:**
  1.  Lakukan pencarian menggunakan setiap model semantik: Word2Vec, FastText, GloVe, dan Ensemble.
  2.  Gunakan fitur "Ekspor ke Excel" untuk setiap hasil pencarian.
  3.  **Verifikasi File Excel (Ensemble):**
      - Pastikan file tidak korup.
      - Cek keberadaan dan kebenaran data di kolom `Peringkat`, `Skor Word2Vec`, `Skor FastText`, `Skor GloVe`.
      - Cek kebenaran metadata di sheet `Informasi Pencarian`.
  4.  **Verifikasi File Excel (Model Tunggal):**
      - Pastikan file tidak korup.
      - Pastikan kolom-kolom khusus ensemble (misalnya, `Skor Word2Vec`) kosong atau tidak ada, dan tidak menyebabkan error.
      - Pastikan `Skor Kesamaan` tetap ada dan benar.
