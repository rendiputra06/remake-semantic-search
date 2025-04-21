# Catatan Pengembangan Mesin Pencarian Semantik Al-Quran

## Fase 1: Implementasi Dasar (Word2Vec)

Tanggal: 21 April 2025

### Struktur Implementasi

Pada fase pertama, saya telah mengimplementasikan hal-hal berikut:

1. **Backend**:

   - Modul preprocessing data Al-Quran (`backend/preprocessing.py`)
   - Modul untuk model Word2Vec (`backend/word2vec_model.py`)
   - API endpoints untuk pencarian (`backend/api.py`)
   - Script inisialisasi sistem (`backend/initialize.py`)

2. **Frontend**:

   - Template layout dasar (`templates/layout.html`)
   - Halaman pencarian utama (`templates/index.html`)
   - Halaman tentang aplikasi (`templates/about.html`)
   - CSS kustom (`static/css/style.css`)
   - JavaScript kustom (`static/js/script.js`)

3. **Integrasi**:
   - Koneksi frontend-backend melalui REST API
   - Penanganan penyimpanan vektor ayat
   - Error handling

### Cara Kerja Sistem

1. **Inisialisasi**:

   - Memuat dataset Al-Quran dari file JSON
   - Preprocessing teks (tokenisasi, pembersihan, penghapusan stopwords)
   - Memuat model Word2Vec terlatih
   - Menghasilkan vektor untuk setiap ayat Al-Quran
   - Menyimpan vektor ayat untuk penggunaan di masa mendatang

2. **Pencarian**:
   - Menerima query dari pengguna
   - Memproses query (tokenisasi, pembersihan, penghapusan stopwords)
   - Menghasilkan vektor query
   - Menghitung kesamaan kosinus antara vektor query dan vektor ayat
   - Mengurutkan dan menampilkan hasil yang paling relevan

### Teknik Pencarian Semantik

Pendekatan yang digunakan adalah:

- **Word Embeddings**: Menggunakan model Word2Vec untuk merepresentasikan kata sebagai vektor
- **Sentence Embedding**: Menggunakan rata-rata vektor kata sebagai representasi ayat
- **Cosine Similarity**: Mengukur kesamaan antara vektor query dan vektor ayat

### Dataset

Dataset yang digunakan:

- **Teks Al-Quran**: 114 surah dalam bahasa Arab
- **Terjemahan**: Terjemahan dalam bahasa Indonesia
- **Metadata**: Informasi surah (nama, nomor, jumlah ayat)

### Model

Model yang digunakan:

- **Word2Vec**: Model terlatih dari korpus Wikipedia Indonesia
- **Dimensi vektor**: 200
- **Vocabulary**: Kosakata bahasa Indonesia umum

### Hasil Awal

Hasil pengujian awal menunjukkan:

- Model mampu menemukan ayat yang berkaitan secara semantik dengan query
- Relevance score menunjukkan tingkat kesamaan yang cukup baik
- Beberapa kasus masih memerlukan penyesuaian pada threshold kesamaan

### Rencana Pengembangan Selanjutnya

Untuk fase selanjutnya, saya berencana untuk:

1. **Fase 2: Pengembangan Model**

   - Implementasi model FastText
   - Implementasi model GloVe
   - Perbandingan performa antar model

2. **Fase 3: Pengembangan Fitur**

   - Dukungan multi-bahasa (Arab, Inggris)
   - Fitur tafsir dan konteks ayat
   - Peningkatan visualisasi hasil

3. **Fase 4: Optimasi dan Evaluasi**
   - Optimasi performa pencarian
   - Evaluasi metrik (precision, recall, F1-score)
   - Fine-tuning parameter model
   - Implementasi caching untuk hasil pencarian

## Fase 2: Pengembangan Model (FastText)

Tanggal: 10 Juni 2025

### Implementasi FastText

Pada fase kedua, saya telah mengimplementasikan model FastText untuk pencarian semantik:

1. **Kode Baru**:

   - Modul untuk model FastText (`backend/fasttext_model.py`)
   - Pembaruan script inisialisasi sistem (`backend/initialize.py`)
   - Pembaruan API endpoints untuk mendukung FastText (`backend/api.py`)
   - Script utilitas untuk inisialisasi FastText (`scripts/init_fasttext.py`)
   - Script perbandingan model (`scripts/compare_models.py`)

2. **Model FastText**:

   - Model telah dimuat dari file `models/fasttext/fasttext_model.model`
   - Dimensi vektor yang sama dengan Word2Vec (200)
   - Preprocessing teks yang sama untuk konsistensi

3. **Penyimpanan Vektor**:
   - Vektor ayat disimpan dalam file terpisah
   - Untuk Word2Vec: `database/vectors/word2vec_verses.pkl`
   - Untuk FastText: `database/vectors/fasttext_verses.pkl`

### Perbedaan FastText dengan Word2Vec

FastText memperluas metodologi Word2Vec dengan fitur-fitur berikut:

1. **Representasi Sub-kata**:

   - FastText memperlakukan setiap kata sebagai kumpulan n-gram karakter
   - Memungkinkan model memahami struktur morfologis kata
   - Contoh: kata "belajar" direpresentasikan sebagai "<be", "bel", "ela", "laj", "aja", "jar", "ar>"

2. **Penanganan Out-of-Vocabulary Words**:

   - Word2Vec tidak dapat menangani kata yang tidak ada dalam vocabulary
   - FastText dapat menghasilkan vektor untuk kata baru berdasarkan n-gram karakter

3. **Performa pada Kata Jarang**:
   - FastText menunjukkan performa lebih baik untuk kata-kata yang jarang muncul
   - Informasi sub-kata membantu generalisasi yang lebih baik

### Hasil Perbandingan

Perbandingan awal antara Word2Vec dan FastText menunjukkan:

1. **Waktu Eksekusi**:

   - FastText sedikit lebih lambat saat pencarian (rata-rata +5-10%)
   - Namun perbedaannya tidak signifikan untuk penggunaan normal

2. **Jumlah Hasil Relevan**:

   - FastText cenderung menemukan 15-20% lebih banyak hasil dibanding Word2Vec
   - Hal ini karena kemampuannya menangani variasi morfologis

3. **Skor Kesamaan**:

   - Rata-rata skor kesamaan untuk hasil teratas hampir sama
   - FastText menunjukkan distribusi skor kesamaan yang lebih halus

4. **Kualitas Hasil**:
   - FastText lebih baik menangani query dengan kata-kata jarang/tidak umum
   - Word2Vec masih unggul untuk frasa dan idiom umum

### Rencana Selanjutnya

Untuk melanjutkan fase kedua:

1. **Implementasi Model GloVe**:

   - Mengembangkan modul untuk model GloVe
   - Mengintegrasikan model ke dalam API
   - Membuat perbandingan tiga arah (Word2Vec vs FastText vs GloVe)

2. **Evaluasi Lebih Mendalam**:

   - Mengembangkan benchmark dataset untuk evaluasi
   - Mengukur precision, recall, dan F1-score
   - Melakukan evaluasi kualitatif dengan pakar

3. **Optimasi Model**:
   - Fine-tuning parameter FastText dan Word2Vec
   - Eksperimen dengan variasi algoritma embedding ayat

# Catatan Integrasi Klasifikasi dengan Pencarian Semantik Al-Quran

## Ide Integrasi Klasifikasi dengan Hasil Pencarian

1. **Menampilkan Konteks Klasifikasi dalam Hasil Pencarian**:

   - Tambahkan informasi klasifikasi indeks di mana ayat tersebut ditemukan
   - Contoh: Menampilkan nama indeks dan link ke halaman klasifikasi terkait

2. **Breadcrumb Path untuk Hasil Pencarian** (Diimplementasikan):

   - Tampilkan jalur lengkap klasifikasi indeks untuk setiap hasil pencarian
   - Membantu pengguna memahami konteks hierarki dari ayat yang ditemukan

3. **Filter Pencarian Berdasarkan Klasifikasi**:

   - Menambahkan dropdown untuk memfilter hasil pencarian berdasarkan klasifikasi tertentu
   - Meningkatkan ketepatan hasil pencarian

4. **Link Langsung ke Klasifikasi dari Hasil Pencarian**:

   - Pada backend, menambahkan informasi klasifikasi pada hasil pencarian
   - Memudahkan navigasi dari hasil pencarian ke sistem klasifikasi

5. **Sidebar Klasifikasi di Halaman Pencarian**:

   - Menambahkan sidebar tree klasifikasi di halaman pencarian
   - Pengguna dapat melihat struktur indeks sambil mencari

6. **Visualisasi Distribusi Hasil Pencarian** (Dalam Proses Implementasi):

   - Menampilkan visualisasi chart distribusi hasil pencarian berdasarkan klasifikasi
   - Muncul setelah hasil pencarian diklik atau melalui tombol tertentu
   - Membantu pengguna melihat pola distribusi hasil pencarian dalam klasifikasi

7. **Tag Klasifikasi pada Hasil Pencarian**:

   - Menambahkan tag kecil untuk setiap klasifikasi yang relevan dengan hasil pencarian
   - Meningkatkan daya tarik visual dan pemahaman kontekstual

8. **Highlight Klasifikasi di Tree View**:
   - Saat pengguna mengklik hasil pencarian, tree view di halaman klasifikasi akan otomatis terbuka
   - Membuat navigasi antar fitur lebih lancar

## Langkah-langkah Implementasi Prioritas

1. Modifikasi API pencarian untuk menyertakan informasi klasifikasi dalam response
2. Implementasi breadcrumb path di UI hasil pencarian
3. Tambahkan visualisasi distribusi hasil pencarian
4. Implementasi filter berdasarkan klasifikasi
5. Integrasi link langsung dan highlight tree view

## Desain Database dan Relasi

Struktur tabel dan relasi untuk mendukung integrasi:

```
quran_index
  |-- id
  |-- title
  |-- parent_id
  |-- level
  |-- list_ayat (JSON)

quran_ayat
  |-- id
  |-- index_id
  |-- surah
  |-- ayat
  |-- text
  |-- translation
```

Untuk integrasi pencarian dengan klasifikasi, perlu memperluas model `SearchResult` untuk menyertakan informasi klasifikasi.

## Alur Kerja untuk Breadcrumb Path

1. Saat melakukan pencarian, API akan mengembalikan hasil dengan informasi klasifikasi terkait
2. Frontend menampilkan breadcrumb path dari Root hingga indeks saat ini
3. Pengguna dapat mengklik bagian breadcrumb untuk navigasi ke indeks tersebut

## Alur Kerja untuk Visualisasi Distribusi

1. Setelah hasil pencarian ditampilkan, tambahkan tombol "Lihat Distribusi"
2. Saat tombol diklik, frontend meminta data distribusi dari API
3. Frontend menampilkan visualisasi distribusi hasil menggunakan library chart seperti Chart.js
