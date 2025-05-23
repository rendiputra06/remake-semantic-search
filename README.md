# Mesin Pencarian Semantik Al-Quran

Aplikasi web untuk mencari ayat-ayat Al-Quran berdasarkan makna menggunakan teknologi pembelajaran mesin dan pemrosesan bahasa alami.

## Fitur Utama

- Pencarian semantik ayat Al-Quran dalam Bahasa Indonesia, Arab, dan Inggris
- Tiga model semantik berbeda (Word2Vec, FastText, dan GloVe)
- Pencarian leksikal (kata kunci, frasa persis, regex)
- Tesaurus sinonim Bahasa Indonesia dan ekspansi query
- Tampilan hasil yang responsif dan interaktif
- Pengaturan lanjutan untuk hasil pencarian

## Teknologi yang Digunakan

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, jQuery
- **Backend**: Flask (Python)
- **Model Semantik**: Word2Vec, FastText, GloVe
- **Pencarian Leksikal**: Inverted Index, Regular Expression
- **Tesaurus**: Sastrawi (Stemming), Tesaurus Bahasa Indonesia

## Cara Menjalankan

1. Clone repositori ini
2. Buat lingkungan virtual Python
   ```
   python -m venv venv
   ```
3. Aktifkan lingkungan virtual
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Pasang dependensi
   ```
   pip install -r requirements.txt
   ```
5. Inisialisasi model
   - Word2Vec saja: `python -m backend.initialize word2vec`
   - FastText saja: `python -m backend.initialize fasttext`
   - Pencarian leksikal: `python -m backend.initialize lexical`
   - Tesaurus sinonim: `python -m backend.initialize thesaurus`
   - Semua model: `python -m backend.initialize all`
   - Atau gunakan script khusus: `python scripts/init_lexical.py`
6. Jalankan aplikasi
   ```
   python app.py
   ```
7. Buka browser dan akses `http://localhost:5000`

## Fase 3: Pengembangan Fitur Lanjutan

Pada fase 3, kami menambahkan fitur pencarian leksikal dan tesaurus sinonim untuk meningkatkan kualitas pencarian. Fitur baru ini menawarkan beberapa keunggulan:

### 1. Pencarian Leksikal

- **Kata Kunci**: Temukan ayat yang mengandung semua kata kunci tertentu
- **Frasa Persis**: Temukan ayat yang mengandung frasa persis seperti yang dicari
- **Regex**: Pencarian lanjutan menggunakan ekspresi reguler untuk pola yang kompleks

### 2. Tesaurus Sinonim Bahasa Indonesia

- Kamus sinonim kata-kata bahasa Indonesia untuk memperkaya pencarian
- Dukungan stemming kata untuk menemukan kata dasar
- Tesaurus khusus untuk istilah-istilah dalam Al-Quran
- Ekspansi query otomatis berdasarkan sinonim

### 3. Pencarian dengan Ekspansi Sinonim

- Memperluas query dengan sinonim secara otomatis
- Menggabungkan hasil dari beberapa query terkait
- Peningkatan recall sambil mempertahankan precision
- Transparansi dengan menampilkan query yang diperluas

### Perbandingan Metode Pencarian

Untuk membandingkan performa metode pencarian yang berbeda, jalankan:

```
python scripts/compare_search_methods.py
```

Script ini akan menghasilkan:

- Tabel perbandingan waktu eksekusi, jumlah hasil, dan efektivitas pencarian
- Analisis kasus penggunaan yang optimal untuk setiap metode
- Grafik visualisasi perbandingan di folder `results/`

## Screenshot

(Akan ditambahkan setelah aplikasi selesai)

## Struktur Proyek

```
semantic-quran-search/
├── app.py                  # File utama aplikasi Flask
├── requirements.txt        # Daftar dependensi
├── backend/                # Kode backend
│   ├── __init__.py
│   ├── api.py              # API endpoint
│   ├── initialize.py       # Inisialisasi sistem
│   ├── preprocessing.py    # Preprocessing data
│   ├── word2vec_model.py   # Model Word2Vec
│   ├── fasttext_model.py   # Model FastText
│   ├── glove_model.py      # Model GloVe
│   ├── lexical_search.py   # Pencarian leksikal
│   └── thesaurus.py        # Tesaurus sinonim
├── models/                 # Model terlatih
│   ├── idwiki_word2vec/    # Model Word2Vec
│   └── fasttext/           # Model FastText
├── database/               # Database
│   ├── vectors/            # Vektor ayat tersimpan
│   ├── lexical/            # Indeks pencarian leksikal
│   └── thesaurus/          # Data tesaurus sinonim
├── dataset/                # Dataset Al-Quran
├── scripts/                # Script utilitas
│   ├── init_fasttext.py    # Script inisialisasi FastText
│   ├── init_lexical.py     # Script inisialisasi Leksikal & Tesaurus
│   └── compare_models.py   # Script perbandingan model
├── results/                # Hasil perbandingan model
├── static/                 # Aset statis
│   ├── css/                # File CSS
│   │   └── style.css       # CSS kustom
│   └── js/                 # File JavaScript
│       └── script.js       # JS kustom
└── templates/              # Template HTML
    ├── layout.html         # Template dasar
    ├── index.html          # Halaman utama (pencarian)
    └── about.html          # Halaman tentang
```

## Status Pengembangan

Proyek ini saat ini berada di Fase 3: Pengembangan Fitur Lanjutan. Implementasi pencarian leksikal dan tesaurus sinonim Bahasa Indonesia telah selesai dan siap digunakan.

## Kontribusi

Kontribusi, saran, dan umpan balik sangat diterima!

## Lisensi

MIT
