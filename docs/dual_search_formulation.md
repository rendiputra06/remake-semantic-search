# Rumusan Pencarian Kombinasi (Dual Search)

Dokumen ini menjelaskan perumusan (formulation) yang dipakai pada fitur "Pencarian Kombinasi Model" yang berada di blueprint `app/dual_search/` dan halaman `templates/dual_search.html`.

## Ringkasan
- Fitur ini mendukung kombinasi 2 model dasar: Word2Vec + FastText (`w2v_ft`), Word2Vec + GloVe (`w2v_glove`), FastText + GloVe (`ft_glove`).
- Fitur ini juga menyediakan opsi Ensemble (3 Model) yang memanfaatkan `backend/ensemble_embedding.py`.
- Menyediakan Ringkasan per-model: total hasil setelah threshold dan daftar Top-N ayat dalam format `Qs.X:Y`.

## Komponen Kode Terkait
- `app/dual_search/__init__.py`
  - Fungsi utama route `/dual-search/search` (POST) yang mengeksekusi pencarian dan penggabungan.
  - Fungsi `_merge_two_model_results(...)` untuk menggabungkan hasil 2 model.
  - Fungsi `_summarize_results(...)` untuk membuat ringkasan per-model.
- `templates/dual_search.html`
  - Template UI untuk menampilkan form, ringkasan model, dan tabel hasil gabungan.
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
    "top_refs": ["Qs.1:1", "Qs.2:255", ...]
  },
  "fasttext": {
    "total": 41,
    "top_refs": ["Qs.3:8", "Qs.1:5", ...]
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
4. Jika `require_both=True`, hanya ayat yang muncul di kedua model (i.e., `a` dan `b` keduanya ada) yang dipertahankan.
5. Hitung skor gabungan (kombinasi sederhana):
   - `model_count = I(a!=None) + I(b!=None)`
   - `sim_base = (a_sim + b_sim) / max(model_count, 1)`
   - Voting bonus: jika `model_count >= 2`, tambahkan `voting_bonus` (default 0.05)
   - `similarity = sim_base + (voting_bonus if model_count>=2 else 0)`
6. Terapkan threshold (jika `threshold is None`, gunakan threshold adaptif P75 dari skor gabungan)
7. Urutkan desc dan batasi dengan `limit` jika diberikan.

Secara matematis untuk 2 model (A dan B):

- Skor dasar kombinasi:
```
sim_base(vid) = (s_A(vid) + s_B(vid)) / C(vid)
C(vid) = I(vid∈A) + I(vid∈B)
```
- Voting bonus:
```
sim(vid) = sim_base(vid) + bonus,  jika C(vid) >= 2
sim(vid) = sim_base(vid),           jika C(vid) < 2
```
- Threshold adaptif (opsional):
```
T = P75({sim(vid) | vid ∈ hasil})  atau fallback 0.5
hasil = { vid | sim(vid) >= T }
```

Catatan:
- Implementasi saat ini menggunakan `require_both=True`, sehingga hanya ayat yang ada di kedua model yang dipertahankan pada kombinasi.
- Parameter `voting_bonus` dapat diatur (default 0.05) jika dibutuhkan.

## Ensemble 3 Model
Untuk opsi `ensemble3`, digunakan `EnsembleEmbeddingModel`:
- Menggabungkan skor dari Word2Vec, FastText, GloVe.
- Dua mode:
  - Weighted averaging + voting bonus (default diaktifkan, `use_voting_filter=True` hanya meloloskan ayat yang muncul di ≥2 model).
  - Meta-ensemble (jika diaktifkan dan model tersedia) melalui `backend/meta_ensemble.py`.

Skor ensemble fallback (tanpa meta):
```
sim_ens(vid) = (w_w2v * s_w2v(vid) + w_ft * s_ft(vid) + w_glove * s_glove(vid)) / (w_w2v + w_ft + w_glove)
Jika jumlah model yang mendeteksi vid ≥ 2, tambahkan voting_bonus
```
Nilai bobot default: `w_w2v = w_ft = w_glove = 1.0`.

## Limit & Total
- Tabel hasil kombinasi menampilkan `min(limit, jumlah_hasil)`.
- Ringkasan per-model menampilkan:
  - Total hasil sebenarnya (menggunakan `limit=None` saat memanggil pencarian per-model).
  - Daftar Top-N sesuai `limit` yang diminta.

## Keputusan Desain
- Memakai threshold adaptif P75 ketika `threshold=None` untuk menjaga relevansi hasil default tanpa konfigurasi manual.
- Menggunakan voting bonus untuk menekankan konsensus lintas model.
- `require_both=True` pada kombinasi 2 model agar hasil lebih presisi (ayat yang disepakati oleh kedua model). Ini bisa dijadikan opsi konfigurasi di masa depan.

## Potensi Pengembangan
- Menjadikan `require_both` sebagai parameter yang bisa ditentukan pengguna (union vs intersection).
- Dukungan bobot khusus per kombinasi (mis. 70% W2V + 30% FT).
- Menampilkan skor per-model pada tabel hasil gabungan (sudah tersedia `individual_scores` di backend; tinggal diekspos ke UI jika diinginkan).
- Menambahkan endpoint API JSON terpisah untuk kombinasi.
