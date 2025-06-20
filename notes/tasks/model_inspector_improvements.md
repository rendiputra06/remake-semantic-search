# Rencana Improvisasi Fitur Model Inspector

## 1. Latar Belakang dan Tujuan

Halaman "Model Inspector" saat ini berfungsi untuk menganalisis representasi satu kata pada satu model. Fungsionalitas ini dapat diperluas secara signifikan untuk menjadi alat analisis dan perbandingan model yang lebih kuat, memberikan wawasan tentang perbedaan cara setiap model (Word2Vec, FastText, GloVe, Ensemble) "memahami" sebuah kata.

**Tujuan Utama:** Mentransformasi halaman "Model Inspector" menjadi **Alat Perbandingan Model** yang memungkinkan pengguna untuk menganalisis dan membandingkan representasi vektor dari sebuah kata pada dua model yang berbeda secara berdampingan.

---

## 2. Analisis dan Rencana Perubahan

### 2.1. Perubahan Konsep & UI/UX

- **Layout Perbandingan:** Antarmuka akan diubah dari satu tampilan menjadi dua kolom (kiri dan kanan). Pengguna dapat memilih satu model untuk setiap kolom.
- **Input Terpusat:** Akan ada satu input kata (`word`) yang berlaku untuk kedua sisi perbandingan.
- **Visualisasi Heatmap:** Diagram batang saat ini akan diganti dengan **heatmap**. Heatmap lebih unggul untuk memvisualisasikan vektor berdimensi tinggi secara ringkas dan memudahkan perbandingan pola antar vektor.
- **Dropdown Dinamis:** Pilihan model akan dimuat dari API (`/api/models/models`) untuk memastikan konsistensi dan kemudahan pemeliharaan.
- **Peningkatan UX:**
  - **Loading State:** Menambahkan spinner pada tombol dan menonaktifkannya selama proses inspeksi.
  - **Error Handling:** Menampilkan pesan error di dalam halaman, menggantikan `alert()` yang mengganggu.

### 2.2. Perubahan Backend

- **Endpoint yang Lebih Fleksibel:** Endpoint `/api/models/inspect` akan dimodifikasi agar bisa memproses permintaan untuk satu atau dua model sekaligus untuk efisiensi.
- **Similar Words untuk Ensemble:** Menambahkan fungsionalitas untuk menemukan kata-kata yang paling mirip (`most_similar`) untuk model `ensemble`, yang saat ini belum ada.

### 2.3. Struktur Respons API yang Diperlukan

Endpoint `/api/models/inspect` akan mengembalikan data untuk kedua model dalam satu respons.

**Contoh permintaan:**

```json
{
  "word": "ilmu",
  "model_left": "word2vec",
  "model_right": "fasttext"
}
```

**Contoh respons:**

```json
{
  "success": true,
  "data": {
    "word": "ilmu",
    "left": {
      "model_type": "word2vec",
      "vector": [...],
      "vector_dimension": 300,
      "vector_norm": 2.5,
      "similar_words": [{"word": "pengetahuan", "similarity": 0.8}]
    },
    "right": {
      "model_type": "fasttext",
      "vector": [...],
      "vector_dimension": 300,
      "vector_norm": 2.8,
      "similar_words": [{"word": "pengetahuan", "similarity": 0.85}]
    }
  }
}
```

---

## 3. Daftar Tugas (Task List)

### Tahap 1: Backend - Modifikasi API Model Inspection

- **File Target:** `app/api/routes/models.py`
- **Tugas:**
  1.  Refactor fungsi `inspect_model` menjadi fungsi pembantu (helper) yang lebih kecil, misal `get_word_inspection_data(word, model_type)`, yang mengembalikan dictionary data inspeksi untuk satu model.
  2.  Modifikasi endpoint `/api/models/inspect` untuk menerima `model_left` dan `model_right`. Panggil helper function untuk masing-masing model.
  3.  Struktur ulang respons JSON agar sesuai dengan format `data: { word, left: {...}, right: {...} }`.
  4.  **(Opsional, Peningkatan)** Implementasikan `similar_words` untuk model `ensemble` dengan mencari tetangga terdekat dari vektor kata di dalam ruang vektor ayat.

### Tahap 2: Frontend - Desain Ulang Halaman Inspeksi

- **File Target:** `templates/model_inspector.html`
- **Tugas:**
  1.  **Struktur HTML:**
      - Ubah `inspectForm` untuk memiliki dua elemen `<select>`: `modelLeft` dan `modelRight`.
      - Buat struktur kontainer dua kolom untuk menampilkan hasil: `resultsLeft` dan `resultsRight`.
      - Setiap kolom hasil akan berisi elemen untuk info dasar, tabel `similar_words`, dan div untuk visualisasi Plotly.
  2.  **Logika JavaScript:**
      - **Muat Model Dinamis:** Saat dokumen siap, panggil API `/api/models/models` dan isi kedua dropdown model.
      - **Update Event Listener:** Ubah event listener form untuk mengambil `word`, `modelLeft`, dan `modelRight`, lalu kirim ke backend.
      - **Terapkan Loading State:** Saat submit, nonaktifkan tombol dan tampilkan spinner. Aktifkan kembali setelah selesai (baik sukses maupun error).
      - **Render Hasil:**
        - Parse respons JSON yang baru.
        - Panggil fungsi render terpisah untuk setiap sisi (kiri dan kanan), misal `renderResults(data.left, 'Left')` dan `renderResults(data.right, 'Right')`.
        - Dalam fungsi render, update info, isi tabel, dan panggil Plotly.
      - **Ganti Visualisasi ke Heatmap:**
        - Ubah `Plotly.newPlot` untuk menggunakan tipe `heatmap`.
        - Konfigurasi data dan layout untuk heatmap (sumbu x, y, dan colorscale). `z: [vector]` akan menjadi data utama.
  3.  **Tampilkan Error:** Tangkap error dan tampilkan pesannya di elemen div khusus error, bukan `alert`.
