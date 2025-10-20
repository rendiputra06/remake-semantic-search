# Rumusan Pencarian Kombinasi (Dual Search)

Dokumen ini menjelaskan perumusan (formulation) yang dipakai pada fitur "Pencarian Kombinasi Model" yang berada di blueprint `app/dual_search/` dan halaman `templates/dual_search.html`.

## Ringkasan
- Fitur ini mendukung kombinasi 2 model dasar: Word2Vec + FastText (`w2v_ft`), Word2Vec + GloVe (`w2v_glove`), FastText + GloVe (`ft_glove`).
- Fitur ini juga menyediakan opsi Ensemble (3 Model) yang memanfaatkan `backend/ensemble_embedding.py`.
- Menyediakan Ringkasan per-model: total hasil setelah threshold dan daftar Top-N ayat dalam format `Qs.X:Y`.
- Menyediakan pengaturan lanjut: intersection/union, voting bonus, bobot model A/B, serta kontrol khusus untuk Ensemble 3 model (metode, voting filter, bobot per model, voting bonus).

## Komponen Kode Terkait
- `app/dual_search/__init__.py`
  - Fungsi utama route `/dual-search/search` (POST) yang mengeksekusi pencarian dan penggabungan.
  - Fungsi `_merge_two_model_results(...)` untuk menggabungkan hasil 2 model.
  - Fungsi `_summarize_results(...)` untuk membuat ringkasan per-model.
  - Route `/dual-search/api/search` untuk API JSON (AJAX).
- `templates/dual_search.html`
  - Template UI untuk menampilkan form, ringkasan model, dan tabel hasil gabungan.
  - Memuat `static/js/dual_search.js` sebagai pemroses interaksi (AJAX, quick search, render dinamis, dsb.).
- `app/api/utils/model_utils.py`
  - Inisialisasi dan pemuatan model-model dasar (`Word2VecModel`, `FastTextModel`, `GloVeModel`). Menggunakan default path backend agar konsisten di Docker.
- Model dasar backend:
  - `backend/word2vec_model.py`
  - `backend/fasttext_model.py`
  - `backend/glove_model.py`
- Ensemble tiga model:
  - `backend/ensemble_embedding.py`

## Preprocessing & Vektorisasi
Setiap model dasar melakukan proses berikut:
1. Preprocess query: `backend.preprocessing.preprocess_text`.
2. Vektor query dan vektor ayat dihitung dengan mean pooling (FastText dapat memakai metode agregasi lain bila diaktifkan: `tfidf`, `hybrid`, `attention`, dll.).
3. Skor kesamaan: cosine similarity antara vektor query dan vektor ayat.
4. Threshold: jika `threshold is None`, digunakan threshold adaptif persentil ke-75 (P75) dari skor pada hasil: `calculate_adaptive_threshold(scores, fallback=0.5)`.

## Ringkasan Per-Model
Untuk menampilkan total hasil sebenarnya dan Top-N referensi ayat per model:
- Panggilan `search(query, limit=None, threshold=...)` pada tiap model untuk mendapatkan keseluruhan hasil setelah threshold.
- Total = `len(results)`.
- Top-N = `results[:N]` dikonversi ke format `Qs.<surah_number>:<ayat_number>`.

Contoh struktur ringkasan (lihat `model_summaries`):
```json
{
  "word2vec": {
    "total": 37,
    "top_refs": ["Qs.1:1", "Qs.2:255", "..."]
  },
  "fasttext": {
    "total": 41,
    "top_refs": ["Qs.3:8", "Qs.1:5", "..."]
  }
}
```

## Penggabungan 2 Model (Dual Search)
Diberikan dua himpunan hasil model yang telah difilter oleh threshold (jika ada):
- A = hasil dari Model A, berupa list dict item per ayat.
- B = hasil dari Model B, serupa dengan A.

Langkah penggabungan:
1. Bentuk map hasil per model berdasarkan `verse_id`:
   - `a = {r['verse_id']: r for r in A}`
   - `b = {r['verse_id']: r for r in B}`
2. Himpun union `ids = set(a.keys()) | set(b.keys())`.
3. Untuk setiap `vid` pada `ids`, ambil skor kesamaan `a_sim` dan `b_sim` (0 jika tidak ada).
4. Mode intersection/union diatur oleh `require_both`:
   - Jika `require_both=True` (intersection), hanya ayat yang muncul di kedua model yang dipertahankan.
   - Jika `require_both=False` (union), ayat yang muncul di salah satu model tetap dipertahankan; skor yang tidak ada dianggap 0 dan skor kombinasi memakai skor yang tersedia atau bobot sesuai ketentuan.
5. Skor gabungan (weighted average) + voting bonus:
   - Jika `a` dan `b` ada: `similarity = (a_sim * a_weight + b_sim * b_weight) / (a_weight + b_weight)`
   - Jika hanya satu ada (union): `similarity = a_sim` atau `b_sim` sesuai ketersediaan.
   - Voting bonus: jika ayat muncul di ≥2 model, tambahkan `voting_bonus`.
6. Terapkan threshold (jika `threshold is None`, gunakan threshold adaptif P75 dari skor gabungan)
7. Urutkan desc dan batasi dengan `limit` jika diberikan.

Secara matematis untuk 2 model (A dan B):

- Skor dasar kombinasi:
```
sim_base(vid) = {
  (a_sim * a_w + b_sim * b_w) / (a_w + b_w), if vid ∈ A ∩ B
  a_sim, if vid ∈ A \ B (union mode)
  b_sim, if vid ∈ B \ A (union mode)
}
```
- Voting bonus:
```
sim(vid) = sim_base(vid) + voting_bonus,  jika C(vid) ≥ 2
sim(vid) = sim_base(vid),                  jika C(vid) < 2
C(vid) = I(vid ∈ A) + I(vid ∈ B)
```
- Threshold adaptif (opsional):
```
T = P75({sim(vid) | vid ∈ hasil})  atau fallback 0.5
hasil = { vid | sim(vid) ≥ T }
```

## Ensemble 3 Model
Untuk opsi `ensemble3`, digunakan `EnsembleEmbeddingModel`:
- Menggabungkan skor dari Word2Vec, FastText, GloVe.
- Dua mode utama:
  - Weighted averaging + voting bonus. Bobot per model dapat diatur: `word2vec_weight`, `fasttext_weight`, `glove_weight`.
  - Meta-ensemble (jika diaktifkan dan model tersedia), melalui `backend/meta_ensemble.py`.
- Voting filter opsional: `use_voting_filter=True` akan meloloskan hanya ayat yang terdeteksi ≥2 model.
- Voting bonus dapat diatur melalui parameter `voting_bonus`.

Skor ensemble fallback (tanpa meta):
```
sim_ens(vid) = (w_w2v * s_w2v(vid) + w_ft * s_ft(vid) + w_glove * s_glove(vid)) / (w_w2v + w_ft + w_glove)
if model_count(vid) ≥ 2: sim_ens(vid) += voting_bonus
```
Nilai bobot default: `w_w2v = w_ft = w_glove = 1.0`.

## Limit & Total
- Tabel hasil kombinasi menampilkan `min(limit, jumlah_hasil)`.
- Ringkasan per-model menampilkan:
  - Total hasil sebenarnya (menggunakan `limit=None` saat memanggil pencarian per-model).
  - Daftar Top-N sesuai `limit` yang diminta.

## API JSON: `/dual-search/api/search`
- Method: POST
- Payload yang didukung:
```json
{
  "query": "...",
  "combo": "w2v_ft" | "w2v_glove" | "ft_glove" | "ensemble3",
  "limit": 10,
  "threshold": 0.5 | null,
  "require_both": true | false,
  "voting_bonus": 0.05,
  "a_weight": 1.0,
  "b_weight": 1.0,
  "method": "weighted" | "meta",            // khusus ensemble3
  "use_voting_filter": true | false,          // khusus ensemble3
  "w2v_weight": 1.0,                          // khusus ensemble3
  "ft_weight": 1.0,                           // khusus ensemble3
  "glove_weight": 1.0                         // khusus ensemble3
}
```
- Respons (ringkas):
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "results": [ { "verse_id": "...", "similarity": 0.87, "surah_number": 2, "ayat_number": 255, ... } ],
    "model_summaries": {
      "word2vec": { "total": 37, "top_refs": ["Qs.1:1", "..."] },
      "fasttext": { "total": 41, "top_refs": ["Qs.3:8", "..."] },
      "glove": { "total": 39, "top_refs": ["Qs.2:2", "..."] }
    },
    "displayed_count": 10,
    "total_combined": 10
  }
}
```

## UI & Interaksi
- Form Dual Search memiliki quick search, input query, combo, limit, threshold, dan panel Pengaturan Lanjutan.
- Panel Pengaturan Lanjutan:
  - 2-Model: intersection/union, voting bonus, bobot A/B.
  - Ensemble: metode (weighted/meta), voting filter, voting bonus, bobot per model.
- AJAX submit ke `/dual-search/api/search`, menampilkan spinner dan render dinamis ringkasan + hasil.
- JavaScript dipisahkan di `static/js/dual_search.js`.

## Keputusan Desain
- Memakai threshold adaptif P75 ketika `threshold=None` untuk menjaga relevansi hasil default tanpa konfigurasi manual.
- Voting bonus untuk menekankan konsensus lintas model.
- `require_both` default `True` pada 2-model (intersection) demi presisi; bisa diubah ke union untuk recall lebih tinggi.
- Kontrol bobot memberi fleksibilitas tuning tanpa merubah backend.

## Potensi Pengembangan
- Modal detail ayat dan tombol ekspor (JSON/CSV) (sebagian sudah tersedia di UI; handler ekspor dapat ditambahkan di JS untuk mengambil data terakhir yang ditampilkan).
- Menyimpan preferensi pengguna (localStorage) agar pengaturan bertahan.
- Opsi agregasi FastText (mean/tfidf/attention) diekspos ke UI.
- Endpoint API evaluasi untuk pengujian batch dan logging.
