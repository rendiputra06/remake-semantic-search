# Cleanup & Maintenance Tasks

## A. Route Cleanup

### 1. Backend API Cleanup

- [x] Backup file `backend/api.py` sebelum penghapusan
- [x] Identifikasi route yang sudah dipindahkan:
  - [x] `/search` -> `app/api/routes/search.py`
  - [x] `/models` -> `app/api/routes/models.py`
  - [x] `/user_settings` -> `app/api/routes/models.py`
  - [x] `/quran/index` -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/tree` -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/all` -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/<int:index_id>` -> `app/api/routes/quran_index.py`
  - [x] `/quran/index` (POST) -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/<int:index_id>` (PUT) -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/<int:index_id>` (DELETE) -> `app/api/routes/quran_index.py`
  - [x] `/quran/excel/sheets` -> `app/api/routes/quran_index.py`
  - [x] `/quran/index/ayat/<int:index_id>` -> `app/api/routes/quran_index.py`
  - [x] `/surah` -> `app/api/routes/quran.py`
  - [x] `/surah/<int:surah_number>` -> `app/api/routes/quran.py`
- [x] Verifikasi fungsi endpoint yang sudah dipindahkan
- [x] Update import statement di file yang masih menggunakan `backend/api.py`
- [x] Hapus route yang tidak digunakan dari `backend/api.py`
- [x] Pindahkan fungsi utilitas ke `app/api/utils/model_utils.py`

### 2. Frontend API Integration

- [x] Audit semua endpoint API yang digunakan di frontend
- [x] Buat mapping antara endpoint lama dan baru:
  - [x] `/api/search` → `/api/search/search`
  - [x] `/api/search/lexical` → `/api/search/search/lexical`
  - [x] `/api/search/expanded` → `/api/search/search/expanded`
  - [x] `/api/models` → `/api/models/models`
  - [x] `/api/user_settings` → `/api/models/user_settings`
  - [x] `/api/statistics/overall` → `/api/statistics/statistics/overall`
  - [x] `/api/statistics/daily` → `/api/statistics/statistics/daily`
  - [x] `/api/quran/index/stats` → `/api/statistics/quran/index/stats`
  - [x] `/api/thesaurus/synonyms` → `/api/thesaurus/synonyms`
  - [x] `/api/thesaurus/add` → `/api/thesaurus/add`
  - [x] `/api/export/excel` → `/api/export/export/excel`
  - [x] `/api/quran/index/<int:index_id>` → `/api/quran/index/index/<int:index_id>`
  - [x] `/api/quran/index` (POST) → `/api/quran/index/index`
  - [x] `/api/quran/index/<int:index_id>` (PUT) → `/api/quran/index/index/<int:index_id>`
  - [x] `/api/quran/index/<int:index_id>` (DELETE) → `/api/quran/index/index/<int:index_id>`
  - [x] `/api/quran/excel/sheets` → `/api/quran/index/excel/sheets`
  - [x] `/api/quran/excel/upload` → `/api/quran/index/excel/upload`
  - [x] `/api/surah` → `/api/quran/surah`
  - [x] `/api/surah/<int:surah_number>` → `/api/quran/surah/<int:surah_number>`
  - [x] `/api/quran/index/ayat/<int:index_id>` → `/api/quran/index/ayat/<int:index_id>`
- [x] Update semua AJAX calls di template untuk menggunakan endpoint baru
- [x] Update JavaScript modules yang menggunakan API
- [ ] Test semua interaksi frontend dengan API baru
- [ ] Dokumentasikan perubahan endpoint untuk referensi tim

## B. Template Improvements

### 1. Error Handling

- [ ] Identifikasi semua template yang memerlukan perbaikan error handling
- [ ] Implementasi error handling yang konsisten di semua template
- [ ] Tambahkan pesan error yang informatif dalam Bahasa Indonesia
- [ ] Perbaiki tampilan error messages di UI
- [ ] Tambahkan logging untuk error di template

### 2. Data Structure

- [ ] Audit struktur data yang dikirim ke template
- [ ] Standardisasi format data untuk setiap template
- [ ] Perbaiki masalah di `admin.html`:
  - [ ] Perbaiki filter `strftime`
  - [ ] Perbaiki struktur data model status
  - [ ] Update tampilan tabel dan form
- [ ] Perbaiki masalah di `settings.html`:
  - [ ] Perbaiki akses atribut `lexical`
  - [ ] Update struktur data pengaturan
  - [ ] Perbaiki validasi form

### 3. Date Formatting

- [ ] Buat custom Jinja2 filter untuk format tanggal
- [ ] Implementasi filter `strftime` yang aman
- [ ] Standardisasi format tanggal di seluruh aplikasi
- [ ] Update semua template yang menggunakan format tanggal
- [ ] Tambahkan timezone handling yang tepat

## C. Documentation & Testing

### 1. API Documentation

- [ ] Setup OpenAPI/Swagger untuk dokumentasi API
- [ ] Dokumentasikan semua endpoint dengan:
  - [ ] Deskripsi endpoint
  - [ ] Parameter yang dibutuhkan
  - [ ] Format response
  - [ ] Contoh request dan response
  - [ ] Error codes dan handling
- [ ] Tambahkan dokumentasi autentikasi
- [ ] Buat panduan penggunaan API

### 2. Testing

- [ ] Setup testing environment
- [ ] Buat test cases untuk:
  - [ ] Unit tests untuk setiap endpoint
  - [ ] Integration tests untuk alur API
  - [ ] Template rendering tests
  - [ ] Error handling tests
- [ ] Implementasi CI/CD pipeline untuk testing
- [ ] Buat test coverage report

## D. Logging & Monitoring

### 1. Error Logging

- [ ] Setup logging system yang proper
- [ ] Implementasi log levels yang sesuai
- [ ] Buat format log yang konsisten
- [ ] Setup log rotation
- [ ] Tambahkan context information di log

### 2. Performance Monitoring

- [ ] Implementasi request timing logging
- [ ] Monitor database query performance
- [ ] Track API endpoint response times
- [ ] Setup alerting untuk error rates
- [ ] Buat dashboard monitoring

## E. Code Quality

### 1. Code Cleanup

- [ ] Lakukan code review menyeluruh
- [ ] Hapus kode yang tidak digunakan
- [ ] Perbaiki code style sesuai standar
- [ ] Optimasi query database
- [ ] Perbaiki security issues

### 2. Dependencies

- [ ] Audit semua dependencies
- [ ] Update dependencies ke versi terbaru
- [ ] Hapus dependencies yang tidak digunakan
- [ ] Dokumentasikan semua dependencies
- [ ] Setup dependency update schedule

## Prioritas Implementasi

1. Template Improvements

   - Error handling di template
   - Perbaikan struktur data
   - Implementasi date formatting

2. Route Cleanup

   - Backend API cleanup
   - Frontend API integration

3. Documentation & Testing

   - API documentation
   - Test implementation

4. Logging & Monitoring

   - Error logging
   - Performance monitoring

5. Code Quality
   - Code cleanup
   - Dependencies management

## Catatan Penting

- Backup semua file sebelum melakukan perubahan besar
- Test setiap perubahan secara menyeluruh
- Dokumentasikan semua perubahan yang dilakukan
- Prioritaskan perbaikan yang mempengaruhi user experience
- Pastikan backward compatibility saat mengubah API
- Gunakan version control dengan baik
- Lakukan code review untuk setiap perubahan besar
- Update dokumentasi sesuai perubahan yang dilakukan
