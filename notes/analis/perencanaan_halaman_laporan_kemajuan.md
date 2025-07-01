# Rencana Pengembangan Halaman Laporan Kemajuan Evaluasi Pencarian

## Tujuan

Menyediakan halaman web untuk monitoring kemajuan dan eksperimen evaluasi pencarian Al-Qur'an berbasis semantic & ontologi, dengan fokus pada angka-angka evaluasi (precision, recall, f1, waktu eksekusi) yang bergerak secara real-time, bukan menampilkan hasil ayat.

## Fitur Utama

- **Input Query & Ayat Relevan**
  - User dapat memasukkan contoh query dan daftar ayat relevan (ground truth) melalui form.
  - Data disimpan di database untuk digunakan pada evaluasi berikutnya.
- **Evaluasi Real-Time**
  - Proses pencarian dijalankan pada berbagai model (Word2Vec, FastText, GloVe, Ontologi) secara real-time.
  - Hanya menampilkan angka evaluasi (precision, recall, f1, waktu eksekusi) yang terus diperbarui saat proses berjalan.
- **Monitoring & Update**
  - User dapat memantau progres evaluasi, memperbarui data query/ayat relevan, dan melihat perubahan skor dari waktu ke waktu.
- **History & Log**
  - Menyimpan riwayat perubahan data dan hasil evaluasi untuk analisis perkembangan model.

## Rencana Arsitektur

### Backend

- Endpoint untuk CRUD query & ayat relevan
- Endpoint untuk trigger evaluasi pencarian pada semua model
- Endpoint untuk mengambil hasil evaluasi (angka-angka evaluasi per model)
- Penyimpanan data query, ayat relevan, dan hasil evaluasi di database

### Frontend

- Form input query & ayat relevan (dengan validasi)
- Tabel/komponen angka evaluasi (precision, recall, f1, waktu eksekusi) per model, update otomatis/live
- Tombol untuk trigger evaluasi ulang
- Komponen history/log perubahan
- UI clean, fokus pada angka dan progres

### Integrasi

- Websocket/polling untuk update angka evaluasi secara live
- Notifikasi jika ada perubahan signifikan pada skor

## Alur Penggunaan

1. User menginput query contoh dan ayat relevan melalui form.
2. Data disimpan ke database.
3. User menekan tombol "Evaluasi" untuk menjalankan proses pencarian pada semua model.
4. Backend menjalankan evaluasi, menghitung precision, recall, f1, waktu eksekusi untuk setiap model.
5. Angka-angka evaluasi ditampilkan secara live di halaman.
6. User dapat memperbarui data, memicu evaluasi ulang, dan memantau progres dari waktu ke waktu.

## Kebutuhan Pengembangan

- **Backend**: Model & endpoint CRUD query/ayat relevan, endpoint evaluasi, penyimpanan hasil, websocket/polling.
- **Frontend**: Form input, tabel angka evaluasi, live update, history/log, notifikasi.
- **Database**: Tabel query, ayat relevan, hasil evaluasi, log perubahan.

## Catatan

- Tidak menampilkan hasil ayat pencarian, hanya angka evaluasi.
- Fokus pada monitoring kemajuan dan eksperimen model.
- Dapat dikembangkan untuk mendukung multi-user dan eksperimen batch.

---

_Dokumen ini sebagai dasar pengembangan halaman laporan kemajuan evaluasi pencarian. Silakan tambahkan detail teknis sesuai kebutuhan implementasi._
