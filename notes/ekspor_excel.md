# Dokumentasi Fitur Ekspor Excel

## Deskripsi

Fitur ekspor Excel memungkinkan pengguna untuk mengekspor hasil pencarian dari mesin pencarian semantik Al-Quran ke dalam format Excel (.xlsx). Fitur ini sangat berguna untuk tujuan penelitian, analisis data, dan dokumentasi hasil pencarian.

## Tujuan

Fitur ini dikembangkan dengan tujuan:

1. **Mendukung Penelitian**: Memungkinkan peneliti untuk menganalisis hasil pencarian dalam jumlah besar tanpa batasan hasil yang ditampilkan di halaman web.
2. **Analisis Data**: Menyediakan format data yang mudah untuk diproses lebih lanjut menggunakan alat analisis data seperti Excel, Python, atau R.
3. **Dokumentasi**: Menyimpan hasil pencarian dalam format yang dapat diakses tanpa koneksi internet setelah ekspor.
4. **Komparasi**: Memudahkan perbandingan hasil dari berbagai metode pencarian (semantik, leksikal, ekspansi sinonim).

## Fitur

1. **Ekspor Tanpa Batasan**: Ekspor semua hasil pencarian tanpa batasan jumlah hasil (tidak seperti tampilan web yang dapat dibatasi).
2. **Format Excel Terstruktur**: Data diorganisir dalam sheet yang berbeda:

   - **Sheet Informasi Pencarian**: Berisi metadata tentang pencarian (query, tipe pencarian, jumlah hasil, waktu ekspor).
   - **Sheet Hasil Pencarian**: Berisi data lengkap dari setiap ayat yang ditemukan.

3. **Informasi Komprehensif**: Ekspor menyertakan semua informasi yang tersedia untuk setiap ayat:

   - Nomor Surah dan nama Surah
   - Nomor Ayat dan referensi (format Surah:Ayat)
   - Teks Arab asli
   - Teks terjemahan dalam Bahasa Indonesia
   - Skor kesamaan (untuk pencarian semantik)
   - Persentase kesamaan
   - Tipe kecocokan (untuk pencarian leksikal)
   - Query sumber (untuk pencarian dengan ekspansi sinonim)
   - Informasi klasifikasi dan hirarki klasifikasi (jika tersedia)

4. **Penamaan File Otomatis**: File Excel yang dihasilkan diberi nama secara otomatis dengan format:
   ```
   Pencarian_{tipe_pencarian}_{query}_{timestamp}.xlsx
   ```
5. **Dukungan untuk Semua Tipe Pencarian**:
   - Pencarian semantik (Word2Vec, FastText, GloVe)
   - Pencarian leksikal (kata kunci, frasa persis, regex)
   - Pencarian dengan ekspansi sinonim

## Cara Penggunaan

1. **Melakukan Pencarian**: Lakukan pencarian seperti biasa menggunakan interface pencarian.
2. **Klik Tombol Ekspor**: Setelah hasil pencarian ditampilkan, klik tombol "Ekspor ke Excel" yang muncul di bagian atas hasil.
3. **Unduh File**: Browser akan mengunduh file Excel yang dapat Anda simpan dan buka dengan aplikasi pengolah spreadsheet.

## Detail Implementasi

### Frontend

Fitur ini diimplementasikan menggunakan kombinasi jQuery untuk mengirim data ke backend dan memproses respons file. Data pencarian dikirimkan dalam format JSON ke endpoint API ekspor.

### Backend

Endpoint API `/api/export/excel` menggunakan library pandas untuk:

1. Mengkonversi data JSON ke dalam DataFrame
2. Menghasilkan file Excel dengan dua sheet (Informasi Pencarian dan Hasil Pencarian)
3. Mengirimkan file ke client menggunakan Flask `send_file`

## Contoh Output

File Excel yang dihasilkan akan memiliki struktur sebagai berikut:

### Sheet 1: Informasi Pencarian

| Informasi       | Nilai                                        |
| --------------- | -------------------------------------------- |
| Query Pencarian | iman kepada allah                            |
| Tipe Pencarian  | semantic                                     |
| Jumlah Hasil    | 25                                           |
| Waktu Ekspor    | 2023-10-25 14:30:45                          |
| Query Diperluas | iman kepada tuhan, percaya kepada allah, ... |

### Sheet 2: Hasil Pencarian

| Surah | Nama Surah | Ayat | Referensi | Teks Arab                            | Terjemahan                              | Skor Kesamaan | Persentase Kesamaan | ... |
| ----- | ---------- | ---- | --------- | ------------------------------------ | --------------------------------------- | ------------- | ------------------- | --- |
| 2     | Al-Baqarah | 3    | 2:3       | الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ... | Mereka yang beriman kepada yang gaib... | 0.85          | 85%                 | ... |
| ...   | ...        | ...  | ...       | ...                                  | ...                                     | ...           | ...                 | ... |

## Manfaat untuk Penelitian

Fitur ini sangat bermanfaat untuk penelitian karena:

1. **Transparansi**: Memungkinkan peneliti untuk melihat dan memverifikasi bobot kesamaan atau metrik kecocokan lainnya.
2. **Reproduktifitas**: Ekspor memungkinkan peneliti untuk mendokumentasikan dan mereproduksi hasil pencarian.
3. **Analisis Lanjutan**: Data dapat diproses lebih lanjut, misalnya untuk menganalisis distribusi skor kesamaan, membandingkan hasil antar model, atau mengidentifikasi pola dalam hasil pencarian.
4. **Perbandingan Kinerja**: Memudahkan perbandingan kinerja berbagai model dan metode pencarian.

## Batasan dan Pertimbangan

1. **Ukuran File**: File ekspor dapat menjadi besar jika hasil pencarian sangat banyak.
2. **Waktu Pemrosesan**: Pencarian dengan jumlah hasil yang sangat besar mungkin memerlukan waktu beberapa saat untuk diproses.
3. **Format Excel**: Saat ini hanya mendukung format Excel (.xlsx). Format lain seperti CSV dapat ditambahkan di kemudian hari jika diperlukan.

## Pengembangan Ke Depan

Fitur ini dapat dikembangkan lebih lanjut dengan:

1. **Opsi Format Tambahan**: Menambahkan dukungan untuk format seperti CSV, JSON, dll.
2. **Kustomisasi**: Memungkinkan pengguna memilih kolom yang ingin diekspor.
3. **Visualisasi Otomatis**: Menambahkan grafik dan visualisasi otomatis berdasarkan hasil pencarian.
4. **Perbandingan Antar Model**: Fitur untuk membandingkan hasil dari berbagai model dalam satu file ekspor.
