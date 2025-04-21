# Backend Mesin Pencarian Semantik Al-Quran

Modul backend untuk mesin pencarian semantik Al-Quran menggunakan model Word2Vec.

## Struktur Direktori

```
backend/
├── __init__.py            # File inisialisasi package
├── api.py                 # Modul untuk API endpoints
├── initialize.py          # Script inisialisasi sistem
├── preprocessing.py       # Modul preprocessing data Al-Quran
├── word2vec_model.py      # Modul untuk model Word2Vec
└── README.md              # Dokumentasi
```

## Cara Inisialisasi Sistem

Untuk menginisialisasi sistem (memproses data Al-Quran dan membuat vektor ayat), jalankan:

```
cd backend
python initialize.py
```

Proses ini perlu dijalankan sekali sebelum menjalankan aplikasi untuk pertama kalinya.

## API Endpoints

### 1. Pencarian (`/api/search`)

**Metode:** POST

**Deskripsi:** Melakukan pencarian semantik ayat Al-Quran

**Parameter:**

- `query` (string): Kata kunci pencarian
- `model` (string): Model semantik yang digunakan (default: "word2vec")
- `language` (string): Bahasa yang digunakan (default: "id")
- `limit` (integer): Batas jumlah hasil (default: 10)
- `threshold` (float): Ambang batas kesamaan (default: 0.5)

**Contoh Request:**

```json
{
  "query": "menyayangi anak yatim",
  "model": "word2vec",
  "language": "id",
  "limit": 5,
  "threshold": 0.5
}
```

**Contoh Response:**

```json
{
  "query": "menyayangi anak yatim",
  "model": "word2vec",
  "results": [
    {
      "verse_id": "93:9",
      "surah_number": "93",
      "surah_name": "Ad-Duha",
      "ayat_number": "9",
      "arabic": "فَأَمَّا الْيَتِيمَ فَلَا تَقْهَرْ",
      "translation": "Maka terhadap anak yatim, janganlah engkau berlaku sewenang-wenang.",
      "similarity": 0.82
    },
    {
      "verse_id": "2:220",
      "surah_number": "2",
      "surah_name": "Al-Baqarah",
      "ayat_number": "220",
      "arabic": "...وَيَسْأَلُونَكَ عَنِ الْيَتَامَى قُلْ إِصْلَاحٌ لَّهُمْ خَيْرٌ...",
      "translation": "...Dan mereka menanyakan kepadamu (Muhammad) tentang anak-anak yatim. Katakanlah, \"Memperbaiki keadaan mereka adalah baik!\"...",
      "similarity": 0.78
    }
  ],
  "count": 2
}
```

### 2. Daftar Model (`/api/models`)

**Metode:** GET

**Deskripsi:** Mendapatkan daftar model semantik yang tersedia

**Response:**

```json
[
  {
    "id": "word2vec",
    "name": "Word2Vec",
    "description": "Model yang mengubah kata menjadi vektor berdasarkan konteks dan mengidentifikasi hubungan semantik antar kata."
  }
]
```

## Alur Kerja Sistem

1. **Preprocessing Data:**

   - Memuat data Al-Quran dari file JSON
   - Ekstraksi ayat dan terjemahan
   - Tokenisasi dan pembersihan teks
   - Penghapusan stopwords

2. **Pembuatan Vektor Ayat:**

   - Memuat model Word2Vec
   - Menghitung vektor ayat sebagai rata-rata vektor kata
   - Menyimpan vektor ayat ke database

3. **Pencarian Semantik:**
   - Praproses query pengguna
   - Hitung vektor query
   - Hitung kesamaan kosinus dengan semua vektor ayat
   - Pilih ayat-ayat dengan kesamaan di atas threshold
   - Urutkan dan kembalikan hasil
