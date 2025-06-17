# Mesin Pencari Semantik Al-Quran

Aplikasi web untuk pencarian ayat Al-Quran menggunakan teknik pencarian semantik dengan model Word2Vec, FastText, dan GloVe. Aplikasi ini juga mendukung pencarian leksikal dan tesaurus sinonim Bahasa Indonesia.

## Fitur Utama

- 🔍 **Pencarian Semantik**: Temukan ayat berdasarkan makna, bukan hanya kata kunci
- 📚 **Multi-Model**: Dukungan untuk Word2Vec, FastText, dan GloVe
- 🔤 **Pencarian Leksikal**: Pencarian berdasarkan kata kunci, frasa, dan regex
- 📖 **Tesaurus Sinonim**: Ekspansi query otomatis dengan sinonim Bahasa Indonesia
- 🎯 **Pencarian Hybrid**: Kombinasi pencarian semantik dan leksikal
- 📊 **Analisis Perbandingan**: Perbandingan performa antar metode pencarian
- 🐳 **Docker Support**: Deployment mudah dengan Docker
- 🔧 **Development Mode**: Hot-reload untuk pengembangan
- 🚀 **Production Ready**: Optimized untuk production dengan Gunicorn

## Teknologi yang Digunakan

- **Backend**: Python Flask
- **AI/ML**: Word2Vec, FastText, GloVe, NLTK
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Container**: Docker & Docker Compose
- **WSGI Server**: Gunicorn (Production)

## Instalasi & Penggunaan

### Opsi 1: Docker (Direkomendasikan)

#### A. Development Mode (Hot-Reload)

Untuk pengembangan dengan hot-reload:

```bash
# Clone repositori
git clone <repository-url>
cd semantic-quran-search

# Jalankan dalam mode development
docker-compose -f docker-compose.dev.yml up --build

# Atau jalankan di background
docker-compose -f docker-compose.dev.yml up -d --build
```

**Keunggulan Development Mode:**

- ✅ Kode berubah secara realtime (hot-reload)
- ✅ Debug mode aktif
- ✅ Volume mounting untuk semua file
- ✅ Flask development server dengan auto-reload
- ✅ Mudah untuk debugging

#### B. Production Mode (Optimized)

Untuk production dengan performa optimal:

```bash
# Clone repositori
git clone <repository-url>
cd semantic-quran-search

# Jalankan dalam mode production
docker-compose up --build

# Atau jalankan di background
docker-compose up -d --build
```

**Keunggulan Production Mode:**

- ✅ Performa optimal dengan Gunicorn
- ✅ Memory usage yang lebih efisien
- ✅ Security yang lebih baik
- ✅ Logging yang terstruktur

#### Langkah Selanjutnya (Setelah Container Berjalan)

1. Tunggu beberapa menit sampai aplikasi siap

   - Flask app akan berjalan di `http://localhost:5000`

2. Inisialisasi model

   ```bash
   # Masuk ke container
   docker-compose exec web bash

   # Jalankan inisialisasi model
   python -m backend.initialize all
   ```

#### Perintah Docker yang Berguna

```bash
# Development mode
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs web
docker-compose -f docker-compose.dev.yml down

# Production mode
docker-compose ps
docker-compose logs web
docker-compose down

# Umum
docker-compose down -v
docker-compose restart
docker-compose exec web bash
```

#### Troubleshooting Docker

- **Docker Desktop tidak berjalan**: Pastikan Docker Desktop sudah dibuka dan status menunjukkan "Docker Desktop is running"
- **Port sudah digunakan**: Pastikan port 5000 tidak digunakan aplikasi lain
- **Build error**: Coba hapus cache dengan `docker system prune -a` lalu build ulang
- **Memory tidak cukup**: Pastikan Docker Desktop memiliki alokasi memory minimal 4GB
- **Hot-reload tidak bekerja**: Pastikan menggunakan `docker-compose.dev.yml` dan volume mounting sudah benar

### Opsi 2: Instalasi Manual

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
   python run.py
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
├── run.py                  # File utama aplikasi Flask
├── requirements.txt        # Daftar dependensi
├── Dockerfile              # Konfigurasi Docker untuk production
├── Dockerfile.dev          # Konfigurasi Docker untuk development
├── docker-compose.yml      # Konfigurasi multi-container production
├── docker-compose.dev.yml  # Konfigurasi multi-container development
├── .dockerignore           # File yang diabaikan saat build Docker
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

Proyek ini saat ini berada di Fase 3: Pengembangan Fitur Lanjutan. Implementasi pencarian leksikal dan tesaurus sinonim Bahasa Indonesia telah selesai dan siap digunakan. Dukungan Docker telah ditambahkan untuk memudahkan deployment dan pengembangan dengan opsi development dan production yang terpisah.

## Kontribusi

Kontribusi, saran, dan umpan balik sangat diterima!

## Lisensi

MIT
