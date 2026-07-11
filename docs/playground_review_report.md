# Laporan Peninjauan Fitur: Data Playground & Ensemble Playground

Saya telah meninjau fungsionalitas, kode sumber, dan alur antarmuka pengguna (**UI**) dari fitur **Data Playground** yang ada pada sistem ini. Peninjauan dilakukan melalui analisis kode backend [playground.py](file:///c:/Users/Rendi/coding/project/semantic/app/api/routes/playground.py), template frontend [playground.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground.html) & [playground_ensemble.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground_ensemble.html), file logika JavaScript [main.js](file:///c:/Users/Rendi/coding/project/semantic/static/js/playground/main.js) & [ensemble.js](file:///c:/Users/Rendi/coding/project/semantic/static/js/playground/ensemble.js), serta pengujian interaktif langsung menggunakan browser subagent.

Berikut adalah temuan lengkap dari hasil peninjauan:

---

## 1. Ringkasan Fitur & Arsitektur
**Data Playground** dirancang dengan tema *Academic Research* yang bersih dan informatif. Fitur ini berfungsi sebagai laboratorium simulasi interaktif untuk melihat bagaimana sistem memproses kueri pencarian semantik ayat Al-Quran secara bertahap (*step-by-step pipeline*).

Sistem ini memiliki **dua halaman playground**:
1. **Standard Data Playground** (`/playground`): Berfokus pada simulasi pencarian menggunakan satu model embedding pilihan (Word2Vec, FastText, atau GloVe).
2. **Ensemble Data Playground** (`/playground/ensemble`): Berfokus pada simulasi penggabungan tiga model dasar secara bersamaan menggunakan bobot kontribusi model (*weighted average*) dan *Voting Filter*.

---

## 2. Alur Eksekusi 7 Langkah (7-Step Pipeline)
Di kedua halaman playground, sisi kanan menampilkan visualisasi alur eksekusi yang dinamis. Mengklik node alur akan langsung merubah tampilan detail kalkulasi di panel kiri secara real-time:

### Langkah 1: Parameter Input (Parameter Masukan)
* Menampilkan ringkasan input simulasi: Kueri aktif, model embedding yang digunakan, nilai threshold saat ini, dan daftar ayat *Ground Truth* (ayat acuan relevan).

### Langkah 2: Pra-pemrosesan Teks (Preprocessing)
* Visualisasi pembersihan teks dari tahap teks mentah (*raw*), konversi huruf kecil (*lowercase*), penghapusan tanda baca, pemisahan kata (*tokenization*), hingga penyaringan kata umum (*stopwords*).
* **Fitur Interaktif Sandbox**: 
  - Pengguna dapat mengklik badge token kata untuk memuat 10 sinonim terdekat dalam ruang vektor model secara langsung (menampilkan *popup* SweetAlert2 menggunakan endpoint `/api/playground/neighbors`).
  - Pengguna dapat mengontrol bobot kata kueri (*Token Weighting*) secara individual menggunakan input angka di samping setiap token untuk mengontrol pengaruh kata tersebut pada pembuatan vektor kueri.

### Langkah 3: Ekstraksi Vektor Kueri
* **Standard**: Menunjukkan rata-rata vektor dari token kata berdimensi 200 yang telah dinormalisasi L2.
* **Ensemble**: Menggabungkan vektor kueri dari ketiga model dasar menggunakan bobot kontribusi model yang diinput oleh user.
* **Visualisasi Ruang Vektor 2D**: Menampilkan grafik sebaran *Scatter Plot* menggunakan **Chart.js**. Dimensi vektor 200D direduksi menjadi koordinat 2D menggunakan metode **SVD (Singular Value Decomposition)** di backend, memperlihatkan jarak spasial antara kueri dengan 10 ayat hasil pencarian terdekat.

### Langkah 4: Perhitungan Cosine Similarity
* **Standard**: Menampilkan tabel top 10 ayat dengan nilai kemiripan kosinus tertinggi.
* **Ensemble**: Menyandingkan skor kemiripan individual (Word2Vec, FastText, GloVe) secara berdampingan dengan skor Ensemble akhir untuk 10 ayat teratas.

### Langkah 5: Penyaringan Threshold & Voting Filter
* **Standard**: Menyaring ayat dengan kemiripan di atas batas threshold aktif.
* **Ensemble**: Selain menyaring berdasarkan threshold, sistem menerapkan **Voting Filter** yang mewajibkan ayat disetujui minimal oleh 2 model dasar. Jika hanya disetujui 1 model, ayat tersebut akan disaring keluar (*filtered out*) untuk menjaga konsistensi makna.

### Langkah 6: Validasi Ground Truth
* Membandingkan hasil pencarian yang lolos filter dengan daftar ayat acuan (*Ground Truth*) dan mengkategorikannya menjadi:
  - 🟢 **True Positive (TP)**: Ayat relevan yang berhasil ditemukan.
  - 🟡 **False Positive (FP)**: Ayat hasil pencarian yang tidak relevan.
  - 🔴 **False Negative (FN)**: Ayat relevan yang gagal ditemukan.

### Langkah 7: Evaluasi Metrik Akhir
* Menghitung dan menampilkan metrik akurasi ilmiah secara real-time: **Precision**, **Recall**, dan **F1-Score**. Rumus matematika perhitungan juga disajikan secara transparan.

---

## 3. Fitur Interaktif & Keunggulan Utama
* **Kalkulasi Client-Side Real-Time**: Data hasil pencarian kasar (top 100) diambil sekali dari server melalui AJAX ke `/api/playground/run`. Setelah data diterima, operasi penyaringan threshold, pencocokan *Ground Truth*, pengelompokan TP/FP/FN, serta perhitungan metrik Precision/Recall/F1 dilakukan langsung di sisi klien (JavaScript). 
* **Sandbox Threshold Slider**: Menggeser slider threshold (misalnya dari `0.50` ke `0.65`) akan langsung memperbarui data pada Langkah 5, 6, dan 7 secara instan tanpa perlu melakukan request ulang ke server.
* **Sandbox Ground Truth Input**: Menambah, menghapus, atau mengedit kode ayat pada input *Ground Truth* (misal: `"2:255, 3:190"`) akan langsung memperbarui klasifikasi TP/FP/FN dan metrik secara instan.
* **Simulate & Reset State**: Tombol reset mengembalikan seluruh state simulasi, bagan, input model weight, dan parameter lainnya ke kondisi default dengan notifikasi pop-up yang ramah pengguna.

---

## 4. Hasil Pengujian Fungsionalitas (Verification Status)
Saya telah melakukan pengujian fungsionalitas penuh di browser pada halaman `/playground` menggunakan kueri **"ilmu"** dengan hasil sebagai berikut:
1. Pemuatan kueri evaluasi dari database ke dalam modal pilihan berjalan lancar.
2. Proses simulasi menghasilkan data preprocessing dan ekstraksi vektor 200 dimensi dengan magnitudo normalisasi L2 sebesar `1.0000`.
3. Chart.js visualisasi ruang vektor 2D berhasil merender titik koordinat SVD secara presisi untuk Kueri dan ayat-ayat terdekat.
4. Perubahan threshold secara interaktif dari `0.50` ke `0.65` berhasil menyaring hasil dari 4 ayat menjadi hanya 1 ayat (`QS Al-A'raf [7]:7` dengan skor similarity `0.6740`).
5. Pembaruan Ground Truth menjadi `"7:7"` secara instan memperbarui metrik keakuratan menjadi **100.0%** untuk Precision, Recall, dan F1-Score.
6. Tidak ditemukan adanya error JavaScript pada console log browser saat simulasi maupun interaksi sandbox dijalankan.
