# Task List Implementasi Halaman Laporan Kemajuan Evaluasi Pencarian

## 1. Database

- [x] Desain tabel `queries` (id, text, created_at)
- [x] Desain tabel `relevant_verses` (id, query_id, verse_ref)
- [x] Desain tabel `evaluation_results` (id, query_id, model, precision, recall, f1, exec_time, evaluated_at)
- [x] Desain tabel `evaluation_log` (id, query_id, model, old_score, new_score, changed_at)

## 2. Backend

- [x] Endpoint CRUD untuk query & ayat relevan
- [x] Endpoint untuk trigger evaluasi pencarian pada semua model
- [x] Endpoint untuk mengambil hasil evaluasi (precision, recall, f1, waktu eksekusi) per model
- [x] Endpoint untuk mengambil history/log perubahan evaluasi

## 3. Frontend

- [x] Form input query & ayat relevan (dengan validasi)
- [x] Tabel angka evaluasi per model (precision, recall, f1, waktu eksekusi), update otomatis/live
- [x] Komponen history/log perubahan
- [ ] UI clean, fokus pada angka dan progres

## 4. Integrasi & Testing

- [x] Uji coba input, evaluasi, dan update live
- [x] Dokumentasi penggunaan halaman

---

**Catatan Progres:**

- Fitur utama CRUD query, ayat relevan, trigger evaluasi, tabel hasil evaluasi, dan log perubahan evaluasi sudah selesai dan terintegrasi frontend-backend.
- Log evaluasi kini otomatis tercatat setiap kali evaluasi dijalankan dan skor berubah.
- Tabel evaluasi otomatis update saat query dipilih.

**Rekomendasi Task Berikutnya:**

- Implementasi endpoint dan tampilan history/log perubahan evaluasi (mengacu pada tabel `evaluation_log`).
- Setelah itu, lanjutkan ke notifikasi perubahan skor dan polling/live update jika ingin monitoring real-time.

Checklist ini dapat diupdate sesuai progres dan kebutuhan implementasi.
