# Task List Pengembangan Fitur ASR Quran (Automatic Speech Recognition)

## Latar Belakang

Aplikasi web untuk menguji dan memberikan umpan balik otomatis pada bacaan Al Quran menggunakan teknologi Automatic Speech Recognition (ASR) berbasis OpenAI Whisper. Cocok untuk latihan santri, guru, maupun pembelajaran mandiri.

## Fitur Utama

- Upload atau rekam audio bacaan Al Quran langsung dari browser
- Transkripsi otomatis bacaan menggunakan model Whisper lokal
- Perbandingan hasil transkripsi dengan ayat referensi (huruf Arab, tanpa/tanpa tanda baca)
- Highlight kesalahan bacaan (benar/salah/tambahan)
- Simpan hasil latihan, waktu, skor, dan detail perbandingan ke database
- Riwayat latihan santri (tabel, skor, detail)
- Mode basic (ayat terbatas, tanpa tanda baca) & lanjutan (seluruh surah, dengan tanda baca)

---

## Task List

### 1. Analisis & Desain

- [x] Analisis kebutuhan user & workflow aplikasi ASR Quran
- [x] Desain skema database latihan, skor, riwayat
- [x] Riset integrasi Whisper lokal (python, ffmpeg, resource)

### 2. Backend API

- [x] Endpoint upload audio/rekaman (accept file & metadata ayat)
- [x] Integrasi Whisper lokal untuk transkripsi audio
- [x] Endpoint untuk membandingkan hasil transkripsi dengan ayat referensi
- [x] Algoritma perbandingan Arab (dengan/tanpa tanda baca), highlight error (benar/salah/tambahan)
- [x] Endpoint simpan hasil latihan (audio, transkrip, skor, detail)
- [x] Endpoint riwayat latihan user (tabel, skor, detail)
- [x] Endpoint GET /api/surah dan /api/ayat (versi ASR Quran)
- [x] Endpoint GET /api/riwayat dan /api/riwayat/<id>
- [x] Endpoint upload+ASR+scoring (POST /asr/upload)
- [ ] Mode basic & lanjutan (filter ayat, pengaturan tanda baca)

### 3. Frontend

- [x] Membuat folder khusus untuk UI ASR Quran (misal: static/js/asr_quran/ dan templates/asr_quran/)
- [x] Komponen upload/rekam audio (browser, UI/UX)
- [x] Pilihan ayat referensi (dropdown/search, terhubung ke endpoint /api/asr_quran/surah dan /api/asr_quran/ayat)
- [x] Form upload audio + metadata (ayat, user, dsb)
- [x] Integrasi upload audio ke endpoint /api/asr_quran/asr/upload
- [x] Tampilkan hasil transkripsi & highlight perbandingan (benar/salah/tambahan)
- [x] Tampilkan skor & detail kesalahan
- [x] Halaman riwayat latihan (tabel, filter, detail, fetch dari /api/asr_quran/riwayat)
- [x] Halaman detail riwayat (fetch dari /api/asr_quran/riwayat/<id>)
- [ ] Pengaturan mode basic/lanjutan (opsional, UI toggle)

### 4. Testing & QA

- [ ] Unit test backend (ASR, perbandingan, scoring)
- [ ] Test upload audio berbagai format/durasi
- [ ] Test highlight error (benar/salah/tambahan)
- [ ] Test riwayat & penyimpanan hasil
- [ ] Uji performa Whisper lokal (resource, waktu proses)
- [ ] Uji integrasi end-to-end (upload → skor → riwayat)

### 5. Dokumentasi & Deployment

- [ ] Dokumentasi API & workflow penggunaan
- [ ] Panduan instalasi Whisper lokal & dependensi
- [ ] Deployment & monitoring resource (CPU/GPU, storage audio)

### 6. Optional/Future

- [ ] Fitur leaderboard/skor antar user
- [ ] Feedback suara (TTS) untuk koreksi bacaan
- [ ] Export hasil latihan (PDF/Excel)

---

## Catatan Progres

- Semua endpoint backend utama untuk workflow ASR Quran sudah tersedia:
  - Upload audio + transkripsi + penilaian otomatis: `POST /api/asr_quran/asr/upload`
  - Daftar surah & ayat: `GET /api/asr_quran/surah`, `GET /api/asr_quran/ayat?surah_id=...`
  - Riwayat latihan: `GET /api/asr_quran/riwayat`, detail: `GET /api/asr_quran/riwayat/<id>`
- Pipeline Whisper lokal, penyimpanan hasil, dan highlight perbandingan sudah terintegrasi.
- Halaman upload dan pengujian bacaan sudah berfungsi dengan baik, termasuk komponen upload audio, pemilihan surah/ayat, dan tampilan hasil.
- Halaman riwayat latihan dan detail riwayat sudah selesai diimplementasikan dengan fitur filter dan tampilan detail lengkap.
- Selanjutnya dapat fokus ke pengembangan mode lanjutan, pengujian menyeluruh, dan dokumentasi.

## Deliverables

1. **Aplikasi ASR Quran**: Web app dengan fitur upload/rekam, transkripsi, perbandingan, highlight, skor, riwayat.
2. **API Backend**: Endpoint upload, transkripsi, perbandingan, simpan hasil, riwayat.
3. **Integrasi Whisper Lokal**: Pipeline ASR lokal, dokumentasi setup.
4. **Dokumentasi**: Panduan penggunaan, instalasi, deployment.
5. **Test & QA**: Unit test, integrasi, validasi performa.

## Timeline (Estimasi)

- Analisis & Desain: 1 minggu
- Backend & Integrasi ASR: 2-3 minggu
- Frontend: 2 minggu
- Testing & QA: 1 minggu
- Dokumentasi & Deployment: 1 minggu

## Petunjuk Penggunaan Aplikasi ASR Quran

### 1. Halaman Upload dan Uji Bacaan

1. **Akses Halaman**: Buka halaman upload ASR Quran melalui menu navigasi atau URL `/asr_quran/upload`
2. **Isi Formulir**:
   - Masukkan nama pengguna pada kolom "Nama User"
   - Pilih surah dari dropdown "Surah"
   - Pilih ayat dari dropdown "Ayat" (dropdown akan terisi otomatis setelah memilih surah)
   - Upload file audio bacaan Al-Quran (format yang didukung: MP3, WAV, M4A, dll)
3. **Proses Pengujian**:
   - Klik tombol "Upload & Uji Bacaan"
   - Sistem akan memproses audio (transkripsi menggunakan Whisper)
   - Tunggu beberapa saat hingga proses selesai
4. **Lihat Hasil**:
   - Hasil transkripsi akan ditampilkan
   - Skor penilaian bacaan akan muncul
   - Ayat referensi akan ditampilkan
   - Highlight perbandingan akan menunjukkan kata-kata yang benar (hijau), salah (merah), atau tambahan (kuning)

### 2. Halaman Riwayat Latihan

1. **Akses Halaman**: Buka halaman riwayat melalui menu navigasi atau URL `/asr_quran/history`
2. **Fitur Filter**:
   - Filter berdasarkan nama pengguna: Masukkan nama pada kolom "Nama User"
   - Filter berdasarkan surah: Pilih surah dari dropdown "Surah"
   - Filter berdasarkan tanggal: Pilih tanggal pada kolom "Tanggal"
   - Klik "Terapkan Filter" untuk menerapkan filter
   - Klik "Reset" untuk menghapus semua filter
3. **Tabel Riwayat**:
   - Menampilkan daftar riwayat latihan dengan kolom: No, Nama, Waktu, Surah, Ayat, Skor, dan Aksi
   - Klik tombol "Detail" untuk melihat detail lengkap latihan

### 3. Halaman Detail Riwayat

1. **Akses Halaman**: Klik tombol "Detail" pada baris riwayat di halaman riwayat latihan
2. **Informasi Umum**:
   - Menampilkan nama pengguna, waktu latihan, surah, dan ayat
3. **Hasil Penilaian**:
   - Skor: Menampilkan nilai hasil penilaian bacaan
   - Audio Rekaman: Player untuk mendengarkan kembali rekaman bacaan
   - Ayat Referensi: Menampilkan teks ayat yang menjadi acuan
   - Transkripsi: Menampilkan hasil transkripsi dari audio
   - Highlight Perbandingan: Menampilkan perbandingan visual antara bacaan dan referensi dengan kode warna (benar, salah, tambahan)
4. **Navigasi**: Klik tombol "Kembali ke Daftar" untuk kembali ke halaman riwayat latihan

### Tips Penggunaan

1. **Kualitas Audio**:
   - Pastikan audio direkam dengan kualitas baik dan minim noise
   - Bacalah dengan jelas dan tidak terlalu cepat untuk hasil transkripsi optimal
2. **Pemilihan Ayat**:
   - Mulailah dengan ayat-ayat pendek untuk latihan awal
   - Pastikan memilih ayat yang sesuai dengan kemampuan
3. **Analisis Hasil**:
   - Perhatikan kata-kata yang ditandai merah (salah) atau kuning (tambahan)
   - Dengarkan kembali rekaman sambil melihat highlight untuk identifikasi kesalahan
   - Lakukan latihan berulang untuk meningkatkan skor

### Keterbatasan Sistem

1. Sistem ASR mungkin tidak 100% akurat dalam mengenali bacaan Arab
2. Hasil transkripsi dapat dipengaruhi oleh kualitas audio, aksen, dan kecepatan bacaan
3. Beberapa tanda baca mungkin tidak terdeteksi dengan sempurna

---

Untuk bantuan lebih lanjut atau melaporkan masalah, silakan hubungi administrator sistem.
