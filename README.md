# Mesin Pencarian Semantik Al-Quran

Aplikasi web untuk mencari ayat-ayat Al-Quran berdasarkan makna menggunakan teknologi pembelajaran mesin dan pemrosesan bahasa alami.

## Fitur Utama

- Pencarian semantik ayat Al-Quran dalam Bahasa Indonesia, Arab, dan Inggris
- Tiga model semantik berbeda (Word2Vec, FastText, dan GloVe)
- Tampilan hasil yang responsif dan interaktif
- Pengaturan lanjutan untuk hasil pencarian

## Teknologi yang Digunakan

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, jQuery
- **Backend**: Flask (Python)
- **Model Semantik**: Word2Vec, FastText, GloVe (dalam pengembangan)

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
   - Semua model: `python -m backend.initialize all`
   - Atau gunakan script khusus: `python scripts/init_fasttext.py`
6. Jalankan aplikasi
   ```
   python app.py
   ```
7. Buka browser dan akses `http://localhost:5000`

## Fase 2: Pengembangan Model

Pada fase 2, kami telah menambahkan model FastText untuk meningkatkan kualitas pencarian semantik. Keunggulan FastText dibandingkan Word2Vec:

1. Dapat menangani kata-kata yang tidak ada dalam kosakata (out-of-vocabulary words)
2. Memanfaatkan informasi sub-kata dan afiks
3. Lebih baik dalam menangani kata-kata jarang atau bahasa morfologis kaya

### Perbandingan Model

Untuk membandingkan performa Word2Vec dan FastText, jalankan:

```
python scripts/compare_models.py
```

Script ini akan menghasilkan:

- Tabel perbandingan waktu eksekusi, jumlah hasil, dan skor kesamaan
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
│   └── fasttext_model.py   # Model FastText
├── models/                 # Model terlatih
│   ├── idwiki_word2vec/    # Model Word2Vec
│   └── fasttext/           # Model FastText
├── database/               # Database
│   └── vectors/            # Vektor ayat tersimpan
├── dataset/                # Dataset Al-Quran
├── scripts/                # Script utilitas
│   ├── init_fasttext.py    # Script inisialisasi FastText
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

Proyek ini saat ini berada di Fase 2: Pengembangan Model. Implementasi model FastText telah selesai dan siap digunakan.

## Kontribusi

Kontribusi, saran, dan umpan balik sangat diterima!

## Lisensi

MIT
