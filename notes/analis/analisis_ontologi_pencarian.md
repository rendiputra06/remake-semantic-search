# Analisis & Perencanaan Pengembangan Fitur Ontologi untuk Pencarian Semantik

## 1. Analisis Proses Pencarian Semantik Saat Ini

- Sistem pencarian semantik saat ini menggunakan model embedding (Word2Vec, FastText, GloVe, Ensemble) untuk mencari ayat yang relevan berdasarkan kemiripan vektor query dan ayat.
- Tidak ada pemahaman relasi konseptual/ontologis antar entitas (misal: sinonim, hierarki konsep, relasi tematik).
- Pencarian hanya berbasis kemiripan statistik, belum reasoning semantik.

## 2. Tujuan Pengembangan Fitur Ontologi

- Memperkaya hasil pencarian dengan pemahaman relasi konseptual (ontologi), seperti sinonim, hiponim, relasi tematik, dsb.
- Mendukung reasoning: pencarian bisa diperluas ke konsep terkait, bukan hanya kemiripan kata.

## 3. Strategi Pengembangan

### a. Desain Ontologi

- Pilih format: RDF/OWL, Graph Database (Neo4j), atau custom JSON/relational.
- Definisikan entitas utama (konsep, tema, entitas, relasi).
- Definisikan relasi: sinonim, antonim, broader/narrower, related-to, dsb.

### b. Integrasi Ontologi ke Proses Pencarian

- Ekspansi query: tambahkan sinonim, konsep terkait dari ontologi.
- Reasoning: jika query mengandung konsep A, hasilkan juga ayat yang mengandung konsep B jika A related-to B.
- Gabungkan hasil pencarian semantik (embedding) dan hasil reasoning ontologi.
- Skor hasil bisa digabungkan (misal: boosting jika ayat mengandung konsep yang secara ontologis relevan).

### c. Pengelolaan Ontologi

- Buat tools/admin page untuk menambah/mengedit konsep dan relasi.
- Sediakan API untuk query ontologi (misal: get related concepts).

### d. Testing & Evaluasi

- Uji hasil pencarian dengan dan tanpa ontologi.
- Lakukan evaluasi relevansi hasil.
