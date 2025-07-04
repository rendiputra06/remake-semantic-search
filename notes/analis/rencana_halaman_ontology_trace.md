# Rencana Halaman Eksperimen: Tracing Pencarian Semantik & Ontologi

## 1. Tujuan Halaman

- Memvisualisasikan dan menampilkan setiap langkah proses pencarian: dari input query, ekspansi ontologi, proses embedding, perhitungan similarity, hingga pemilihan ayat hasil.
- Menampilkan data mentah (angka embedding, similarity, query ekspansi, dsb) dan logika pengambilan keputusan di setiap tahap.
- Memudahkan peneliti untuk memahami, menganalisis, dan membandingkan hasil serta proses di balik mesin pencarian.

---

## 2. Fitur Utama Halaman

### a. Form Input

- Input query, pilihan model (word2vec, fasttext, glove, ensemble), limit hasil.
- Tombol "Trace" untuk memulai proses.

### b. Step-by-Step Panel (Accordion/Timeline)

- Setiap langkah proses ditampilkan sebagai panel/timeline yang bisa diexpand/collapse:
  1. Input Query: Query asli, model, limit.
  2. Ekspansi Ontologi: Konsep utama, label, sinonim, related, hasil ekspansi (list), data konsep yang ditemukan.
  3. Word Embedding: Vektor embedding query & ekspansi (angka, tabel/array), jika ensemble tampilkan semua model.
  4. Similarity Calculation: Perhitungan similarity antara query/ekspansi dengan ayat-ayat (top-N), angka similarity mentah, ayat target, sumber query.
  5. Boosting & Ranking: Proses boosting skor, urutan hasil akhir.
  6. Hasil Akhir: List ayat hasil, skor, sumber query, info relevan lain.

### c. Log/Debug Console

- Panel khusus untuk menampilkan log print/debug dari backend (JSON, tabel, atau teks).

### d. Visualisasi

- Bubble net sederhana untuk memperjelas relasi query-ekspansi-ayat.

---

## 3. Rencana Implementasi Teknis

### a. Frontend

- Template baru: `templates/ontology_trace.html`
- JS: AJAX ke endpoint baru, render step-by-step, tampilkan data mentah (angka, array, JSON).
- Komponen UI: Accordion/timeline (Bootstrap), tabel angka, panel log, visualisasi (opsional).

### b. Backend

- Endpoint baru: `/api/ontology/trace` (POST)
- Modifikasi/extend service pencarian:
  - Pada setiap langkah utama (ekspansi, embedding, similarity, ranking), kumpulkan data intermediate.
  - Return response JSON yang berisi: query, model, expanded_queries, data konsep, embedding (array angka), similarity matrix, ranking, hasil akhir, dan log proses.
- Opsional: Tambahkan mode debug/log pada SearchService dan OntologyService.

### c. Contoh Struktur Response API

```json
{
  "query": "iman",
  "model": "word2vec",
  "expanded_queries": ["iman", "percaya", "aqidah"],
  "ontology_data": [{...}],
  "embeddings": {
    "query": [0.12, -0.34, ...],
    "expanded": {
      "percaya": [0.11, -0.32, ...],
      ...
    }
  },
  "similarities": [
    {"ayat": "2:255", "similarity": 0.87, "source_query": "iman", "embedding": [...]},
    ...
  ],
  "boosting": [
    {"ayat": "2:255", "original": 0.87, "boosted": 0.97, "source_query": "percaya"}
  ],
  "final_results": [...],
  "logs": [
    "Query: iman",
    "Ekspansi: ['iman', 'percaya', 'aqidah']",
    "Embedding query: [0.12, -0.34, ...]",
    "Similarity 2:255: 0.87 (iman), 0.79 (percaya)",
    ...
  ]
}
```

---

## 4. Langkah Implementasi

1. Buat template baru: `ontology_trace.html` (copy dari ontology_search, modifikasi untuk step-by-step).
2. Buat endpoint baru: `/api/ontology/trace` (POST).
3. Modifikasi/extend SearchService & OntologyService:
   - Tambahkan parameter `trace=True` untuk mengumpulkan data intermediate.
   - Pada setiap langkah, simpan data ke dict log/trace.
4. Frontend:
   - Kirim request ke endpoint trace.
   - Render setiap step dan data intermediate secara interaktif.
5. Testing:
   - Uji dengan berbagai query, model, dan limit.
   - Pastikan semua data intermediate tampil dan mudah dianalisis.

---

## 5. Nilai Tambah untuk Penelitian

- Transparansi penuh: Setiap angka dan keputusan bisa dilihat dan diverifikasi.
- Mudah untuk analisis dan debugging.
- Bisa digunakan untuk presentasi, dokumentasi, atau pengujian model baru.
