# Task List Implementasi Fitur Ontologi untuk Pencarian Semantik

## 1. Analisis & Desain

- [x] Analisis kebutuhan ontologi (domain, cakupan, relasi utama)
- [x] Pilih format penyimpanan ontologi (RDF/OWL, Neo4j, JSON, dsb)
- [x] Rancang skema ontologi (entitas, relasi, properti)

## 2. Implementasi Dasar Ontologi

- [x] Buat struktur data ontologi (file atau database)
- [x] Implementasikan loader dan query API untuk ontologi
- [x] Tambahkan endpoint API untuk query ontologi (misal: `/api/ontology/related`)

## 3. Integrasi ke Proses Pencarian

- [x] Modifikasi pipeline pencarian:
  - [x] Ekspansi query dengan sinonim/relasi dari ontologi
  - [x] Gabungkan hasil pencarian semantik dan reasoning ontologi
  - [x] Skor hasil gabungan (misal: boosting)
- [x] Tambahkan parameter di frontend untuk mengaktifkan pencarian berbasis ontologi (halaman baru khusus)

## 4. Admin & Pengelolaan Ontologi

- [ ] Buat halaman admin untuk CRUD konsep dan relasi ontologi
- [ ] Implementasikan validasi dan visualisasi relasi

## 5. Testing & Evaluasi

- [ ] Uji hasil pencarian dengan berbagai skenario
- [ ] Lakukan evaluasi relevansi dan perbaiki jika perlu

## 6. Dokumentasi

- [ ] Dokumentasikan arsitektur, API, dan cara penggunaan fitur ontologi
