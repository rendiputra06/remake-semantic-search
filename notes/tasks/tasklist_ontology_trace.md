# Task List Implementasi Halaman Tracing Pencarian Semantik & Ontologi

## 1. Persiapan & Perancangan

- [ ] Review rencana dan kebutuhan fitur tracing
- [ ] Identifikasi bagian kode yang perlu di-modifikasi (service, API, template)

## 2. Backend

- [x] Buat endpoint baru `/api/ontology/trace` (POST)
      _Endpoint kerangka awal sudah dibuat di `app/api/routes/ontology.py`_
- [x] Extend/duplikasi fungsi pencarian di SearchService & OntologyService agar mendukung mode tracing (mengumpulkan data intermediate di setiap langkah)
      _Tracing dasar pada proses pencarian semantik sudah terintegrasi di SearchService dan endpoint /trace._
- [x] Tambahkan parameter opsional `trace=True` pada fungsi pencarian
      _Sudah diterapkan pada SearchService.semantic_search._
- [x] Pada setiap langkah utama (ekspansi, embedding, similarity, ranking), simpan data intermediate ke dict trace/log
      _Enrichment trace pada proses ekspansi ontologi, pencarian semantik, dan boosting sudah diterapkan di endpoint /trace._
- [ ] Return response JSON lengkap (query, model, expanded_queries, data konsep, embedding, similarity, ranking, hasil akhir, log)
- [ ] Tambahkan logging/debug print jika diperlukan

## 3. Frontend

- [x] Buat template baru `templates/ontology_trace.html` (bisa copy dari ontology\*search)
      _Template dasar dengan form, panel step-by-step, dan log sudah dibuat._
- [x] Tambahkan form input (query, model, limit, tombol Trace)
      _Form input sudah terintegrasi di template ontology_trace.html._
- [x] Implementasi AJAX ke endpoint `/api/ontology/trace`
      _AJAX sudah terintegrasi di template ontology_trace.html._
- [x] Render hasil tracing dalam bentuk step-by-step (accordion/timeline/panel)
      _Frontend sudah menampilkan trace step-by-step dengan nested accordion._
- [x] Tampilkan data mentah (angka embedding, similarity, dsb) dalam tabel/array
      _Frontend sudah menampilkan data intermediate (array/tabel/JSON) secara informatif._
- [x] Tampilkan log/debug console
      _Log proses tracing sudah tampil jelas di panel khusus di frontend._
- [x] (Opsional) Tambahkan visualisasi bubble net sederhana
      _Visualisasi bubble net sudah terintegrasi di halaman tracing menggunakan vis-network._

## 4. Testing & Validasi

- [ ] Uji dengan berbagai query, model, dan limit
- [ ] Pastikan semua data intermediate tampil dan mudah dianalisis
- [ ] Validasi hasil tracing sesuai dengan proses backend

## 5. Dokumentasi

- [ ] Update README/rencana jika ada perubahan signifikan
- [ ] Tambahkan contoh penggunaan halaman tracing untuk penelitian
