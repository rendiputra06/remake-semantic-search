# Script Pengayaan Tesaurus Bahasa Indonesia

Kumpulan alat untuk memperkaya tesaurus sinonim bahasa Indonesia dengan teknik web scraping dan pengolahan data statis.

## Persyaratan

Sebelum menggunakan script ini, pastikan Anda telah menginstal semua dependensi yang diperlukan:

```bash
pip install beautifulsoup4 requests tqdm sastrawi
```

## Struktur File

- `enrich_thesaurus.py` - Script utama untuk pengayaan tesaurus dari berbagai sumber
- `wordlist_generator.py` - Script untuk menghasilkan daftar kata umum dari dataset
- `static_thesaurus_data.csv` - Data statis yang berisi pasangan kata dan sinonimnya

## Cara Penggunaan

### 1. Menghasilkan Daftar Kata

Script `wordlist_generator.py` digunakan untuk menghasilkan daftar kata umum Bahasa Indonesia dari berbagai dataset. Daftar kata ini akan digunakan sebagai input ke script pengayaan tesaurus.

```bash
python wordlist_generator.py --quran-dataset ../dataset --output common_words.txt --stem
```

Parameter yang tersedia:

- `--input-dir` - Direktori berisi file teks untuk ekstraksi kata
- `--quran-dataset` - Path ke direktori dataset Al-Quran
- `--output` - Path untuk file output (default: wordlist.txt)
- `--min-length` - Panjang minimum kata (default: 3)
- `--min-frequency` - Frekuensi minimum kemunculan kata (default: 2)
- `--stem` - Jika ditentukan, akan menghasilkan kata dasar menggunakan stemmer Sastrawi

### 2. Memperkaya Tesaurus

Script `enrich_thesaurus.py` digunakan untuk memperkaya tesaurus dengan sinonim dari berbagai sumber seperti situs web dan data statis.

```bash
python enrich_thesaurus.py --input common_words.txt --limit 100
```

Parameter yang tersedia:

- `--input` - File berisi daftar kata untuk dicari sinonimnya
- `--limit` - Batas jumlah kata yang diproses (default: 50)
- `--thesaurus-path` - Path ke file pickle tesaurus (default: ../database/thesaurus/id_thesaurus.pkl)
- `--custom-path` - Path ke file JSON tesaurus kustom (default: ../database/thesaurus/custom_thesaurus.json)

### 3. Pemrosesan Data Statis

Anda juga dapat memperkaya tesaurus menggunakan data statis dari file CSV:

```bash
python enrich_thesaurus.py --static-data static_thesaurus_data.csv
```

## Sumber Data

Script ini menggunakan beberapa sumber data untuk memperkaya tesaurus:

1. **Web Scraping** dari:

   - sinonimkata.com
   - persamaankata.com
   - tesaurus.kemdikbud.go.id
   - artikel merdeka.com tentang sinonim

2. **Data Statis** dari:
   - File CSV dengan format: `kata,sinonim1,sinonim2,...`
   - Dataset Al-Quran (terjemahan Bahasa Indonesia)

## Keluaran

Script menghasilkan dua file keluaran utama:

1. **id_thesaurus.pkl** - File pickle berisi seluruh tesaurus
2. **custom_thesaurus.json** - File JSON berisi sinonim kustom yang bisa diedit

Selain itu, script juga menghasilkan file log `enrichment_log.txt` yang mencatat statistik pengayaan.

## Catatan Penting

- Pastikan untuk bersikap sopan saat melakukan web scraping dengan menambahkan delay antar permintaan
- Gunakan parameter `--limit` untuk membatasi jumlah kata yang diproses terutama saat melakukan web scraping
- Periksa dan sesuaikan daftar sinonim dari sources web scraping karena bisa saja ada kesalahan

## Contoh Alur Kerja

1. Hasilkan daftar kata umum dari dataset Al-Quran:

   ```bash
   python wordlist_generator.py --quran-dataset ../dataset --output quran_words.txt --stem
   ```

2. Perkaya tesaurus menggunakan data statis:

   ```bash
   python enrich_thesaurus.py --static-data static_thesaurus_data.csv
   ```

3. Perkaya tesaurus lebih lanjut dengan web scraping:

   ```bash
   python enrich_thesaurus.py --input quran_words.txt --limit 100
   ```

4. Periksa hasil pengayaan di file log:
   ```bash
   cat enrichment_log.txt
   ```
