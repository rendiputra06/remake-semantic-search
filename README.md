# Mesin Pencari Semantik Al-Quran

Aplikasi web untuk pencarian ayat Al-Quran menggunakan teknik pencarian semantik dengan model Word2Vec, FastText, GloVe, dan <strong>Ensemble (Averaging)</strong>. Aplikasi ini juga mendukung pencarian leksikal dan tesaurus sinonim Bahasa Indonesia.

## Fitur Utama

- 🔍 **Pencarian Semantik**: Temukan ayat berdasarkan makna, bukan hanya kata kunci
- 📚 **Multi-Model**: Dukungan untuk Word2Vec, FastText, GloVe, dan <strong>Ensemble (Averaging)</strong>
- 🔤 **Pencarian Leksikal**: Pencarian berdasarkan kata kunci, frasa, dan regex
- 📖 **Tesaurus Sinonim**: Ekspansi query otomatis dengan sinonim Bahasa Indonesia
- 🎯 **Pencarian Hybrid**: Kombinasi pencarian semantik dan leksikal
- 📊 **Analisis Perbandingan**: Perbandingan performa antar metode pencarian
- 🐳 **Docker Support**: Deployment mudah dengan Docker
- 🔧 **Development Mode**: Hot-reload untuk pengembangan
- 🚀 **Production Ready**: Optimized untuk production dengan Gunicorn

## Fitur Ensemble (Averaging)

- **Ensemble (Averaging)** menggabungkan hasil Word2Vec, FastText, dan GloVe secara rata-rata (averaging) untuk meningkatkan robustnes dan akurasi pencarian semantik.
- Dapat dipilih pada halaman utama melalui dropdown "Model Semantik".
- Mendukung ekspor hasil pencarian ke Excel seperti model lain.
- Cocok untuk pencarian makna yang lebih general dan hasil yang lebih stabil.

## Cara Menggunakan Fitur Ensemble

1. Buka halaman utama aplikasi.
2. Pilih "Semantik" pada dropdown "Tipe Pencarian".
3. Pilih "Ensemble (Averaging)" pada dropdown "Model Semantik".
4. Masukkan kata kunci pencarian dan klik "Cari".
5. Hasil pencarian akan menggunakan gabungan ketiga model.
6. Untuk ekspor hasil ke Excel, klik tombol "Ekspor ke Excel" di atas hasil pencarian.

## API Endpoint (Pencarian Semantik)

- Endpoint: `/api/search/search` (POST)
- Parameter `model` dapat diisi dengan: `word2vec`, `fasttext`, `glove`, atau `ensemble`.
- Response dan format ekspor Excel sama untuk semua model.

**Contoh Request:**

```json
{
  "query": "menyayangi anak yatim",
  "model": "ensemble",
  "language": "id",
  "limit": 5,
  "threshold": 0.5
}
```

**Contoh Response:**

```json
{
  "query": "menyayangi anak yatim",
  "model": "ensemble",
  "results": [ ... ],
  "count": 2
}
```

## Ekspor Hasil ke Excel

- Hasil pencarian (termasuk dengan model ensemble) dapat diekspor ke Excel dengan tombol "Ekspor ke Excel" di halaman hasil pencarian.
- File Excel akan berisi semua kolom hasil, skor kesamaan, dan informasi klasifikasi jika tersedia.

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
   - Semua model: `


# Menjalankan script import menggunakan Docker
docker-compose exec -T web python3 scripts/import_quran.py

# Output berhasil:
✅ Berhasil import 114 surah
✅ Berhasil import 6,236 ayat
✅ Database sekarang terisi lengkap
# Test berbagai ayat - SEMUA BERHASIL! ✅

curl "http://localhost:5000/api/quran/ayat_detail?surah=1&ayat=1"
✅ Success: Ayat 1:1 (Al-Fatihah)

curl "http://localhost:5000/api/quran/ayat_detail?surah=2&ayat=255"  
✅ Success: Ayat 2:255 (Ayat Kursi)

curl "http://localhost:5000/api/quran/ayat_detail?surah=114&ayat=6"
✅ Success: Ayat 114:6 (An-Nas)