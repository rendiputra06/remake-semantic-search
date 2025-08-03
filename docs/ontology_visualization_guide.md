# Panduan Visualisasi Ontologi Al-Quran

## Overview

Halaman Visualisasi Ontologi Al-Quran adalah fitur baru yang memungkinkan pengguna untuk mengeksplorasi konsep-konsep dalam Al-Quran melalui berbagai jenis visualisasi interaktif yang lebih cocok untuk data ontologi. Halaman ini berbeda dari halaman pencarian ontologi yang ada karena fokus pada visualisasi data ontologi dengan metode yang lebih informatif dan sesuai dengan struktur relasi ontologi.

## Fitur Utama

### 1. Jenis Visualisasi

#### Bubble Network
- Visualisasi network dengan node berbentuk lingkaran (bubble)
- Node size berdasarkan jumlah relasi konsep
- Warna node berdasarkan tipe konsep (broader, narrower, related)
- Fisika simulasi untuk layout otomatis yang optimal
- Edge berbeda untuk relasi broader (panah hijau), narrower (panah kuning), dan related (garis merah)

#### Hierarchical Tree
- Visualisasi hierarki berdasarkan relasi broader/narrower
- Layout top-down yang jelas menunjukkan struktur
- Node berbentuk box untuk readability yang lebih baik
- Edge dengan panah menunjukkan arah relasi
- Cocok untuk melihat struktur hierarkis ontologi

#### Force-Directed Graph
- Simulasi fisika untuk layout yang natural
- Node size proporsional dengan kompleksitas konsep
- Edge yang smooth dan interaktif
- Layout yang dinamis dan responsif
- Cocok untuk eksplorasi relasi yang kompleks

#### Tabel Konsep
- Tampilan tabular yang informatif
- Kolom lengkap: ID, Label, Sinonim, Broader, Narrower, Related, Ayat
- Badge berwarna untuk setiap elemen relasi
- Hover effect dan click untuk detail
- Cocok untuk analisis data yang detail

#### Kartu Konsep
- Tampilan card-based yang modern
- Informasi ringkas per konsep
- Statistik relasi yang mudah dibaca
- Layout responsive untuk berbagai device
- Cocok untuk overview cepat dan browsing

### 2. Panel Kontrol

#### Jenis Visualisasi
- Dropdown untuk memilih jenis visualisasi
- Perubahan real-time tanpa reload halaman
- 5 opsi visualisasi yang berbeda dan cocok untuk ontologi

#### Pencarian Konsep
- Search box untuk mencari konsep spesifik
- Filter real-time berdasarkan:
  - Label konsep
  - ID konsep
  - Sinonim konsep
- Reset otomatis ke semua data jika search kosong

#### Filter Relasi
- Checkbox untuk filter tipe relasi:
  - **Broader**: Konsep yang lebih luas
  - **Narrower**: Konsep yang lebih spesifik
  - **Related**: Konsep yang terkait
- Kontrol real-time untuk fokus pada relasi tertentu
- Kombinasi filter untuk analisis yang lebih spesifik

#### Tombol Muat Data
- Reload data ontologi dari server
- Update statistik dan visualisasi
- Loading indicator selama proses

### 3. Statistik Dashboard

#### Total Konsep
- Menampilkan jumlah total konsep dalam ontologi
- Update real-time saat data berubah

#### Total Relasi
- Menghitung semua relasi (broader, narrower, related)
- Memberikan insight tentang kompleksitas ontologi

#### Total Ayat
- Jumlah total ayat yang terkait dengan semua konsep
- Indikator kelengkapan data ontologi

#### Kedalaman
- Menampilkan kedalaman maksimal hierarki
- Kontrol untuk membatasi kompleksitas visualisasi

### 4. Interaksi

#### Zoom Controls
- **Zoom In**: Memperbesar visualisasi
- **Zoom Out**: Memperkecil visualisasi
- **Fit View**: Menyesuaikan view ke seluruh data

#### Detail Konsep
- Klik node/row/card untuk melihat detail konsep
- Modal dengan informasi lengkap:
  - Informasi dasar (ID, Label, Jumlah Ayat)
  - Sinonim konsep
  - Ayat terkait
  - Konsep broader (lebih luas)
  - Konsep narrower (lebih spesifik)
  - Konsep related (terkait)

#### Filter Konsep Terkait
- Tombol "Lihat Konsep Terkait" di modal
- Filter visualisasi hanya menampilkan konsep yang berelasi
- Memudahkan eksplorasi relasi antar konsep

#### Hover Effects
- Highlight node yang terhubung saat hover
- Tooltip dengan informasi detail konsep
- Visual feedback yang responsif

## Teknologi yang Digunakan

### Frontend
- **Vis.js**: Untuk network graph dengan fisika simulasi yang optimal
- **Bootstrap 5**: Untuk UI/UX yang responsif
- **Font Awesome**: Untuk ikon yang konsisten

### Backend
- **Flask**: Framework web
- **SQLite**: Database untuk menyimpan data ontologi
- **JSON**: Format data ontologi

## Struktur File

```
templates/
├── ontology_visualization.html    # Template halaman utama
static/
├── js/
│   └── ontology_visualization.js  # JavaScript untuk visualisasi
run.py                             # Route untuk halaman (/ontology-visualization)
```

## API Endpoints

### GET /ontology-visualization
- Route untuk halaman visualisasi ontologi
- Tidak memerlukan autentikasi (public)
- Render template dengan user context

### GET /api/ontology/admin/all
- Endpoint untuk mengambil semua data ontologi
- Digunakan oleh JavaScript untuk memuat data
- Response: `{success: true, concepts: [...]}`

## Cara Penggunaan

### 1. Akses Halaman
- Buka browser dan akses `/ontology-visualization`
- Atau klik menu "Pencarian" > "Visualisasi Ontologi"

### 2. Pilih Visualisasi
- Gunakan dropdown "Jenis Visualisasi"
- Pilih salah satu dari 5 opsi yang tersedia:
  - **Bubble Network**: Untuk overview relasi
  - **Hierarchical Tree**: Untuk struktur hierarki
  - **Force-Directed Graph**: Untuk eksplorasi kompleks
  - **Tabel Konsep**: Untuk analisis detail
  - **Kartu Konsep**: Untuk browsing cepat

### 3. Gunakan Filter
- Aktifkan/nonaktifkan checkbox filter relasi
- Kombinasikan filter untuk fokus analisis
- Lihat feedback toast untuk konfirmasi filter

### 4. Eksplorasi Data
- Klik node/row/card untuk melihat detail konsep
- Gunakan zoom controls untuk navigasi
- Gunakan search box untuk filter konsep
- Hover untuk melihat tooltip

### 5. Analisis Relasi
- Klik node untuk melihat detail
- Klik "Lihat Konsep Terkait" untuk filter
- Eksplorasi relasi antar konsep
- Gunakan filter untuk fokus pada relasi tertentu

## Keunggulan

### 1. Visualisasi yang Cocok untuk Ontologi
- 5 jenis visualisasi yang dirancang khusus untuk data ontologi
- Setiap jenis memberikan perspektif berbeda tentang struktur relasi
- Cocok untuk berbagai kebutuhan analisis ontologi

### 2. Interaktif dan Responsif
- Zoom, pan, dan navigasi yang smooth
- Detail on-click untuk setiap konsep
- Filter dan search real-time
- Hover effects yang informatif

### 3. Filter yang Fleksibel
- Kontrol granular untuk tipe relasi
- Kombinasi filter untuk analisis spesifik
- Feedback visual untuk konfirmasi filter
- Reset otomatis untuk eksplorasi ulang

### 4. Informasi yang Komprehensif
- Statistik dashboard yang lengkap
- Detail konsep yang komprehensif
- Relasi antar konsep yang jelas
- Tooltip yang informatif

### 5. User Experience yang Baik
- Design yang responsive untuk berbagai device
- Performance yang optimal untuk data besar
- Loading indicator yang user-friendly
- Toast notification untuk feedback

## Perbedaan dengan Halaman Ontologi Lainnya

### vs Halaman Pencarian Ontologi (/ontology)
- **Fokus**: Visualisasi vs Pencarian
- **Interaksi**: Eksplorasi vs Query-based
- **Output**: Visual vs Text-based results
- **Use Case**: Analisis vs Search

### vs Halaman Admin Ontologi (/admin/ontology)
- **Akses**: Public vs Admin only
- **Fungsi**: View-only vs CRUD operations
- **Audience**: End users vs Administrators
- **Complexity**: Simple vs Advanced management

## Perbandingan Jenis Visualisasi

### Bubble Network
- **Kelebihan**: Overview yang baik, node size informatif, warna yang bermakna
- **Kekurangan**: Bisa crowded untuk data besar
- **Best Use**: Overview relasi, analisis kompleksitas

### Hierarchical Tree
- **Kelebihan**: Struktur hierarki yang jelas, mudah dibaca
- **Kekurangan**: Terbatas pada relasi broader/narrower
- **Best Use**: Analisis struktur hierarki, taxonomy

### Force-Directed Graph
- **Kelebihan**: Layout natural, eksplorasi yang dinamis
- **Kekurangan**: Layout tidak deterministik
- **Best Use**: Eksplorasi relasi kompleks, discovery

### Tabel Konsep
- **Kelebihan**: Informasi lengkap, mudah dibandingkan
- **Kekurangan**: Tidak visual, terbatas pada data tabular
- **Best Use**: Analisis detail, comparison

### Kartu Konsep
- **Kelebihan**: Modern, responsive, overview cepat
- **Kekurangan**: Informasi terbatas per card
- **Best Use**: Browsing, overview cepat

## Roadmap Pengembangan

### Fitur yang Direncanakan
1. **Export Visualisasi**: Save sebagai PNG/SVG
2. **Custom Color Scheme**: Pilihan warna tema
3. **Animation**: Transisi smooth antar visualisasi
4. **Mobile Optimization**: Touch gestures untuk mobile
5. **Performance**: Virtualization untuk data besar
6. **Analytics**: Tracking penggunaan visualisasi

### Integrasi
1. **Search Integration**: Link ke halaman pencarian
2. **Admin Integration**: Quick edit dari visualisasi
3. **API Enhancement**: Endpoint khusus untuk visualisasi
4. **Caching**: Cache data untuk performance

## Troubleshooting

### Masalah Umum

#### Data Tidak Muncul
- Cek koneksi internet
- Refresh halaman
- Cek console browser untuk error
- Pastikan endpoint `/api/ontology/admin/all` berfungsi

#### Visualisasi Lambat
- Kurangi jumlah data dengan search
- Gunakan visualisasi yang lebih sederhana (table/cards)
- Cek performance browser

#### Node Tidak Klik
- Pastikan JavaScript berfungsi
- Cek console untuk error
- Refresh halaman

#### Filter Tidak Berfungsi
- Pastikan checkbox filter tercentang
- Cek console untuk error JavaScript
- Refresh halaman

### Debug Mode
- Buka Developer Tools (F12)
- Cek Console untuk error
- Cek Network tab untuk API calls
- Cek Elements untuk DOM structure

## Kesimpulan

Halaman Visualisasi Ontologi Al-Quran memberikan cara baru untuk mengeksplorasi dan memahami struktur konsep dalam Al-Quran. Dengan 5 jenis visualisasi yang dirancang khusus untuk data ontologi, pengguna dapat melihat data ontologi dari berbagai perspektif dan mendapatkan insight yang lebih mendalam tentang relasi antar konsep.

Fitur filter yang fleksibel dan interaksi yang responsif membuat halaman ini sangat cocok untuk analisis ontologi yang mendalam, sambil tetap mempertahankan kemudahan penggunaan untuk pengguna umum.

Fitur ini melengkapi sistem pencarian semantik yang sudah ada dengan memberikan tools visualisasi yang powerful untuk analisis dan eksplorasi data ontologi. 