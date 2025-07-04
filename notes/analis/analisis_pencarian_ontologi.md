# Analisis Fitur: Pencarian Ontologi (`/ontology`)

## 1. Deskripsi Umum

Halaman `/ontology` adalah antarmuka pencarian ontologi berbasis Al-Qur'an yang memungkinkan pengguna melakukan pencarian konsep secara semantik, dengan ekspansi query berbasis ontologi (label, sinonim, dan relasi terkait). Hasil pencarian divisualisasikan dalam bentuk daftar ayat dan bubble net relasi konsep.

---

## 2. Alur Kerja Frontend

- **Template:** `templates/ontology_search.html`
- **Fitur Utama:**

  - Quick search (tag kata kunci populer)
  - Form pencarian (input kata kunci, pilihan model, limit hasil)
  - Hasil pencarian (list ayat, info ekspansi query)
  - Visualisasi relasi (bubble net dengan vis-network)

- **Interaksi Utama:**
  - Saat form disubmit, JavaScript akan melakukan `fetch` ke endpoint `/api/ontology/search` (POST) dengan body `{ query, model, limit }`.
  - Hasil dari backend akan ditampilkan sebagai:
    - Daftar ayat hasil pencarian (dengan skor similarity, sumber query, dsb)
    - Info ekspansi query (badge konsep hasil ekspansi)
    - Visualisasi bubble net (node: query utama, ekspansi, ayat; edge: relasi antar node)

---

## 3. Alur Backend

### a. Routing

- **Route Halaman:**  
  Didefinisikan di `run.py`:
  ```python
  @app.route('/ontology')
  def ontology_search():
      ...
      return render_template('ontology_search.html', user=user)
  ```
- **API Endpoint:**  
  Didefinisikan di blueprint `ontology_bp` (`app/api/routes/ontology.py`), diregister dengan prefix `/api/ontology`:
  ```python
  @ontology_bp.route('/search', methods=['POST'])
  def ontology_search():
      ...
  ```

### b. Proses Pencarian (API `/api/ontology/search`)

- **Input:**  
  JSON `{ query, model, limit }`
- **Langkah:**
  1. **Ekspansi Query:**
     - Cari konsep utama (`find_concept`) berdasarkan label, id, atau sinonim.
     - Jika ditemukan, ekspansi dengan label, sinonim, dan related.
     - Jika tidak, coba ekspansi per kata dalam query.
  2. **Pencarian Semantik:**
     - Untuk setiap query hasil ekspansi, lakukan pencarian semantik (`search_service.semantic_search`) dengan model yang dipilih (word2vec, fasttext, glove, ensemble).
     - Hasil dari semua query digabungkan, jika ayat ditemukan dari ekspansi (bukan query utama), skor similarity di-boost.
  3. **Pengembalian Hasil:**
     - Hasil diurutkan berdasarkan similarity, dibatasi sesuai limit.
     - Response: `{ success, query, expanded_queries, results, count }`
     - Setiap result memuat info ayat, similarity, sumber query, status boosted, dsb.

### c. Service Layer

- **OntologyService:**

  - Menyimpan dan memuat konsep dari JSON/database.
  - Fungsi utama: `find_concept`, `get_related`, `get_all`, `add/update/delete_concept`.
  - Mendukung switching storage (JSON <-> database) dan audit trail perubahan konsep.

- **SearchService:**
  - Mengelola pencarian semantik (Word2Vec, FastText, GloVe, Ensemble).
  - Fungsi utama: `semantic_search(query, model_type, ...)` yang mengembalikan ayat-ayat relevan beserta skor similarity.

---

## 4. Struktur Data Konsep Ontologi

Setiap konsep memiliki struktur:

```json
{
  "id": "unik",
  "label": "nama konsep",
  "synonyms": ["sinonim1", "sinonim2"],
  "broader": ["id_konsep_broader"],
  "narrower": ["id_konsep_narrower"],
  "related": ["id_konsep_terkait"],
  "verses": ["2:255", ...]
}
```

Disimpan di database (`ontology_concepts`) atau file JSON (`ontology/ontology.json`).

---

## 5. Visualisasi Bubble Net

- Menggunakan library `vis-network`.
- Node utama: query, node hijau: ekspansi, node abu/kuning: ayat hasil pencarian.
- Edge: relasi antar query-ekspansi dan ekspansi/utama-ke-ayat.

---

## 6. Fitur Manajemen & Maintenance

- **Switch Storage:**  
  Admin dapat berpindah antara penyimpanan JSON dan database, serta melakukan sinkronisasi data.
- **Audit Trail:**  
  Setiap perubahan konsep dicatat (khusus mode database).
- **Backup & Recovery:**  
  Script migrasi dan verifikasi data tersedia di `scripts/`.

---

## 7. Catatan & Saran Pengembangan

- **Ekspansi query** sangat penting untuk meningkatkan recall pencarian semantik.
- **Model ensemble** dapat meningkatkan akurasi hasil.
- **Audit trail** dan backup otomatis penting untuk keamanan data ontologi.
- **Visualisasi** sangat membantu pemahaman relasi konsep bagi user.

---

## 8. Referensi File Terkait

- `templates/ontology_search.html`
- `app/api/routes/ontology.py`
- `app/api/services/ontology_service.py`
- `app/api/services/search_service.py`
- `ontology/ontology.json` atau database `ontology_concepts`
- `run.py` (route utama)
- `scripts/migrate_ontology_to_db.py`, `scripts/verify_ontology_db.py`
