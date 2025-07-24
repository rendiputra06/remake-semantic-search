# Analisis Proses Pencarian Ontologi

## 1. Halaman Evaluasi (`/evaluasi`)

-   **Frontend**: `static/js/evaluasi.js`
-   **Endpoint yang digunakan**: `/api/evaluation/<selectedQueryId>/run` (POST)
-   **Payload**:
    -   `query_text`: Teks query yang dievaluasi
    -   `result_limit`: Batas jumlah hasil (bisa tak terbatas)
    -   `threshold_per_model`: Threshold untuk setiap model, termasuk `ontology`
    -   `selected_methods`: Metode yang dipilih untuk evaluasi
-   **Proses**:
    -   Frontend mengambil default settings threshold dari `/api/models/default_settings`.
    -   Setelah threshold didapat, frontend mengirim request ke `/api/evaluation/<selectedQueryId>/run` dengan payload di atas.
    -   Backend melakukan evaluasi query pada berbagai model (word2vec, fasttext, glove, ensemble, ontology, dll) sesuai threshold dan metode yang dipilih.
    -   Hasil evaluasi, termasuk hasil dari model ontologi, dikembalikan ke frontend untuk ditampilkan.

## 1. Halaman Evaluasi (`/evaluasi`) - Metode Ontologi

-   **Frontend**: `static/js/evaluasi.js`
-   **Pemilihan Metode**: Pengguna dapat memilih satu atau beberapa metode evaluasi, salah satunya adalah "ontology".
-   **Proses Saat Metode Ontologi Dipilih**:
    -   Frontend akan menambahkan "ontology" ke dalam array `selected_methods`.
    -   Payload yang dikirim ke backend pada endpoint `/api/evaluation/<selectedQueryId>/run`:
        -   `query_text`: Teks query yang dievaluasi
        -   `result_limit`: Batas jumlah hasil
        -   `threshold_per_model`: Threshold untuk setiap model, termasuk `ontology`
        -   `selected_methods`: Berisi "ontology" jika dipilih
    -   Backend akan menjalankan evaluasi query menggunakan model ontologi sesuai threshold dan parameter lain.
    -   Hasil evaluasi ontologi akan dikembalikan bersama hasil model lain (jika dipilih).
-   **Karakteristik**:
    -   Proses evaluasi ontologi dilakukan dalam satu request bersama model lain (multi-model).
    -   Hasil evaluasi ontologi biasanya berupa skor, relevansi, dan perbandingan dengan model lain.
    -   Cocok untuk membandingkan performa ontologi dengan model embedding lain.

## 2. Halaman Pencarian Ontologi (`/ontology`)

-   **Frontend**: `templates/ontology_search.html` (JavaScript inline)
-   **Proses Pencarian**:
    -   Pengguna mengisi form pencarian dan memilih model (biasanya hanya "ontology" atau varian lain).
    -   Payload yang dikirim ke endpoint `/api/ontology/search`:
        -   `query`: Teks query pencarian
        -   `model`: Model yang digunakan (biasanya "ontology")
        -   `limit`: Batas jumlah hasil
    -   Backend melakukan pencarian ontologi berdasarkan query dan model.
    -   Hasil pencarian langsung dikembalikan dan ditampilkan (biasanya berupa daftar konsep, relasi, atau hasil pencocokan ontologi).
-   **Karakteristik**:
    -   Proses pencarian ontologi dilakukan secara spesifik dan langsung.
    -   Hasil pencarian lebih fokus pada hasil ontologi saja, tanpa perbandingan dengan model lain.
    -   Cocok untuk eksplorasi dan penelusuran konsep ontologi.

## 3. Perbandingan Detail

| Aspek              | Evaluasi (Metode Ontologi)              | Pencarian Ontologi (Halaman Ontology) |
| ------------------ | --------------------------------------- | ------------------------------------- |
| Endpoint           | `/api/evaluation/<id>/run`              | `/api/ontology/search`                |
| Payload            | query, threshold, selected_methods      | query, model, limit                   |
| Proses Backend     | Evaluasi multi-model, termasuk ontologi | Pencarian ontologi spesifik           |
| Output             | Skor, relevansi, perbandingan model     | Daftar hasil pencarian ontologi       |
| Tujuan             | Analisis performa & perbandingan model  | Eksplorasi & penelusuran ontologi     |
| Interaksi Pengguna | Pilih beberapa metode sekaligus         | Pilih model & query spesifik          |

**Kesimpulan Detail:**

-   Metode ontologi di evaluasi adalah bagian dari proses evaluasi multi-model, hasilnya bisa dibandingkan dengan model lain.
-   Pencarian ontologi di halaman ontology adalah proses pencarian langsung, hasilnya hanya dari model ontologi.
-   Jika ingin hasil dan proses yang konsisten, perlu penyesuaian endpoint dan payload agar logika backend seragam.
