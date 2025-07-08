# Perbaikan Halaman Settings dan Evaluasi

## Ringkasan Perubahan

Perubahan ini memindahkan pengaturan `result_limit` dan `threshold` dari halaman evaluasi ke halaman settings, dan menghilangkan pilihan model dari halaman settings. Pengaturan ini sekarang berlaku untuk semua model pencarian.

## Perubahan yang Dilakukan

### 1. Halaman Settings (`/settings`)

#### Perubahan Template (`templates/settings.html`)

- **Menghilangkan pilihan model**: Dihapus dropdown untuk memilih model default
- **Menambahkan opsi "Tak Terbatas"**: Ditambahkan opsi dengan nilai 0 untuk jumlah hasil tak terbatas
- **Menambahkan penjelasan**: Ditambahkan form-text untuk menjelaskan bahwa pengaturan berlaku untuk semua model
- **Menambahkan opsi 100 hasil**: Ditambahkan pilihan 100 hasil sebagai opsi tambahan

#### Perubahan Backend (`run.py`)

- **Menghilangkan default_model dari form**: Route settings tidak lagi mengambil default_model dari form
- **Menggunakan default_model yang ada**: Menggunakan default_model yang sudah tersimpan di database

#### Perubahan Database (`backend/db.py`)

- **Validasi input**: Ditambahkan validasi untuk result_limit dan threshold
- **Menangani nilai 0**: Nilai 0 untuk result_limit dianggap sebagai "tak terbatas"

### 2. Halaman Evaluasi (`/evaluasi`)

#### Perubahan Template (`templates/evaluasi.html`)

- **Menyembunyikan input result_limit dan threshold**: Dihapus input field untuk limit dan threshold
- **Memperbesar input query**: Input query diperbesar dari col-md-5 menjadi col-md-9
- **Menyederhanakan form**: Form evaluasi menjadi lebih sederhana

#### Perubahan JavaScript (`static/js/evaluasi.js`)

- **Menggunakan pengaturan dari database**: JavaScript mengambil pengaturan result_limit dan threshold dari API `/api/models/user_settings`
- **Fallback ke nilai default**: Jika gagal mengambil pengaturan, menggunakan nilai default (limit: 10, threshold: 0.5)
- **Menangani nilai tak terbatas**: Nilai 0 untuk result_limit dikonversi menjadi 1000 sebagai limit maksimal

### 3. API dan Services

#### Perubahan Search Service (`app/api/services/search_service.py`)

- **Parameter opsional**: Limit dan threshold menjadi parameter opsional
- **Menggunakan pengaturan user**: Jika parameter tidak diberikan, mengambil dari pengaturan user
- **Menangani nilai tak terbatas**: Nilai 0 untuk result_limit dikonversi menjadi 1000

#### Perubahan Search Routes (`app/api/routes/search.py`)

- **Parameter opsional**: Limit dan threshold menjadi parameter opsional
- **Menggunakan pengaturan database**: Jika parameter tidak diberikan, menggunakan pengaturan dari database
- **Menangani expanded search**: Expanded search juga menggunakan pengaturan dari database

#### Perubahan Ontology Routes (`app/api/routes/ontology.py`)

- **Parameter opsional**: Limit dan threshold menjadi parameter opsional
- **Menggunakan pengaturan database**: Ontology search menggunakan pengaturan dari database

#### Perubahan Models API (`app/api/routes/models.py`)

- **Menangani nilai tak terbatas**: Endpoint user_settings mengkonversi nilai 0 menjadi 1000

## Fitur Baru

### 1. Pengaturan Global

- **Semua model menggunakan pengaturan yang sama**: Word2Vec, FastText, GloVe, Ensemble, dan Ontologi menggunakan pengaturan result_limit dan threshold yang sama
- **Pengaturan tersimpan per user**: Setiap user memiliki pengaturan sendiri yang tersimpan di database

### 2. Opsi "Tak Terbatas"

- **Nilai 0 = Tak Terbatas**: Pengguna dapat memilih "Tak Terbatas" untuk jumlah hasil
- **Limit maksimal 1000**: Untuk performa, nilai tak terbatas dibatasi maksimal 1000 hasil

### 3. Validasi Input

- **Validasi result_limit**: Tidak boleh negatif
- **Validasi threshold**: Harus antara 0 dan 1

## Cara Penggunaan

### 1. Mengatur Pengaturan Global

1. Buka halaman `/settings`
2. Pilih jumlah hasil default (5, 10, 20, 50, 100, atau Tak Terbatas)
3. Atur ambang kesamaan menggunakan slider (0.1 - 0.9)
4. Klik "Simpan Pengaturan"

### 2. Menggunakan Evaluasi

1. Buka halaman `/evaluasi`
2. Pilih query evaluasi dari dropdown
3. Pilih metode evaluasi yang diinginkan
4. Klik "Jalankan Evaluasi"
5. Sistem akan menggunakan pengaturan dari halaman settings

### 3. Pencarian Semantik

1. Lakukan pencarian di halaman utama
2. Sistem akan menggunakan pengaturan dari database
3. Jika ingin override, dapat memberikan parameter limit dan threshold dalam request API

## Keuntungan

### 1. Konsistensi

- **Pengaturan seragam**: Semua model menggunakan pengaturan yang sama
- **Tidak ada kebingungan**: User tidak perlu mengatur pengaturan untuk setiap model

### 2. Kemudahan Penggunaan

- **Interface yang lebih sederhana**: Halaman evaluasi menjadi lebih bersih
- **Pengaturan terpusat**: Semua pengaturan ada di satu tempat

### 3. Fleksibilitas

- **Opsi tak terbatas**: User dapat memilih untuk mendapatkan semua hasil yang relevan
- **Override tetap mungkin**: API masih mendukung override parameter

## File yang Diubah

1. `templates/settings.html` - Template halaman settings
2. `templates/evaluasi.html` - Template halaman evaluasi
3. `static/js/evaluasi.js` - JavaScript halaman evaluasi
4. `run.py` - Route settings
5. `backend/db.py` - Database functions
6. `app/api/services/search_service.py` - Search service
7. `app/api/routes/search.py` - Search routes
8. `app/api/routes/ontology.py` - Ontology routes
9. `app/api/routes/models.py` - Models API

## Testing

### 1. Test Pengaturan Settings

- Test menyimpan pengaturan dengan berbagai nilai
- Test validasi input (nilai negatif, threshold di luar range)
- Test opsi "Tak Terbatas"

### 2. Test Evaluasi

- Test evaluasi menggunakan pengaturan dari database
- Test fallback ke nilai default jika gagal ambil pengaturan
- Test dengan berbagai metode evaluasi

### 3. Test Pencarian

- Test pencarian semantik menggunakan pengaturan dari database
- Test override parameter dalam API
- Test ontology search dan expanded search

## Catatan Penting

1. **Nilai 0 = Tak Terbatas**: Dalam database, nilai 0 disimpan untuk representasi "tak terbatas"
2. **Limit Maksimal 1000**: Untuk performa, nilai tak terbatas dibatasi maksimal 1000 hasil
3. **Backward Compatibility**: API tetap mendukung parameter limit dan threshold untuk override
4. **User Settings**: Pengaturan disimpan per user, jadi setiap user memiliki pengaturan sendiri
