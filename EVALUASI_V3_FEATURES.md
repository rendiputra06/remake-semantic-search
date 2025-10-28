# Evaluasi V3 - Advanced Ensemble Configuration

## 📋 Ringkasan
Evaluasi V3 adalah versi lanjutan dari sistem evaluasi yang menambahkan konfigurasi ensemble yang sangat detail dan fitur-fitur analisis canggih untuk meningkatkan akurasi dan fleksibilitas pengujian model.

## 🎯 Fitur Utama yang Ditambahkan

### 1. **Pengaturan Ensemble Lanjutan**
Terinspirasi dari halaman `ensemble-test`, evaluasi v3 menambahkan kontrol penuh atas konfigurasi ensemble:

#### a. Bobot Model yang Dapat Disesuaikan
- **Word2Vec Weight** (0.0 - 2.0): Kontrol pengaruh model Word2Vec
- **FastText Weight** (0.0 - 2.0): Kontrol pengaruh model FastText  
- **GloVe Weight** (0.0 - 2.0): Kontrol pengaruh model GloVe
- Slider interaktif dengan indikator pengaruh (Disabled, Low, Reduced, Normal, Enhanced, High)

#### b. Metode Ensemble
- **Weighted Averaging**: Rata-rata tertimbang dengan bobot kustom
- **Voting**: Equal weights dengan filter voting (≥2 model)
- **Meta-Ensemble**: Machine learning-based prediction
- **Semua (Perbandingan)**: Jalankan semua metode dan bandingkan hasilnya

#### c. Parameter Tambahan
- **Voting Bonus** (0.0 - 0.5): Bonus skor untuk ayat yang muncul di ≥2 model
- **Voting Filter**: Toggle untuk hanya menampilkan ayat dari minimal 2 model
- **Threshold per Model**: Kontrol threshold untuk setiap model secara independen

### 2. **Quick Presets**
Konfigurasi siap pakai untuk berbagai skenario:

- **Balanced**: Konfigurasi seimbang (1.0, 1.0, 1.0)
- **Precision Focus**: Optimasi untuk precision tinggi (1.2, 1.0, 0.8, threshold 0.6)
- **Recall Focus**: Optimasi untuk recall tinggi (1.0, 1.2, 1.0, threshold 0.4)
- **Conservative**: Pendekatan konservatif dengan voting filter (0.8, 0.8, 1.2, threshold 0.65)
- **Aggressive**: Pendekatan agresif untuk hasil maksimal (1.5, 1.3, 1.0, threshold 0.35)

### 3. **Perbandingan Metode Ensemble**
Ketika memilih "Semua (Perbandingan)", sistem akan:
- Menjalankan evaluasi dengan semua metode ensemble
- Menampilkan perbandingan side-by-side
- Menandai metode terbaik untuk setiap metrik (★)
- Memberikan analisis:
  - Best Precision
  - Best Recall
  - Best F1-Score
  - Fastest Execution

### 4. **Mode Visualisasi yang Ditingkatkan**
Tiga mode tampilan hasil:

#### a. Table View
- Tabel lengkap dengan semua metrik
- Highlight untuk metode terbaik
- Informasi konfigurasi ensemble

#### b. Chart View
- Bar chart interaktif untuk Precision, Recall, F1-Score
- Perbandingan visual antar metode
- Powered by Chart.js

#### c. Comparison View
- Kartu perbandingan detail untuk setiap metode ensemble
- Metric cards dengan color coding
- Informasi bobot dan parameter

### 5. **API Endpoints Tambahan**

#### a. `/api/evaluation_v3/<query_id>/run` (POST)
Endpoint utama untuk evaluasi dengan konfigurasi lanjutan.

**Request Body:**
```json
{
  "query_text": "ibadah",
  "result_limit": 10,
  "selected_methods": ["lexical", "word2vec", "fasttext", "glove", "ensemble"],
  "ensemble_config": {
    "method": "weighted",
    "w2v_weight": 1.2,
    "ft_weight": 1.0,
    "glove_weight": 0.8,
    "voting_bonus": 0.05,
    "use_voting_filter": false
  },
  "threshold_per_model": {
    "ensemble": 0.5,
    "word2vec": 0.5,
    "fasttext": 0.5,
    "glove": 0.5
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "ensemble_comparison": {
    "Weighted Averaging": {...},
    "Voting": {...},
    "Meta-Ensemble": {...}
  },
  "ensemble_analysis": {
    "best_precision": ["Meta-Ensemble", {...}],
    "best_recall": ["Voting", {...}],
    "best_f1": ["Weighted Averaging", {...}],
    "fastest": ["Weighted Averaging", {...}]
  },
  "config": {...}
}
```

#### b. `/api/evaluation_v3/<query_id>/compare-thresholds` (POST)
Analisis sensitivitas threshold.

**Request Body:**
```json
{
  "query_text": "shalat",
  "model_type": "ensemble",
  "threshold_range": [0.3, 0.4, 0.5, 0.6, 0.7],
  "result_limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "model_type": "ensemble",
  "results": [
    {
      "threshold": 0.3,
      "metrics": {
        "precision": 0.75,
        "recall": 0.85,
        "f1": 0.80
      },
      "exec_time": 0.234,
      "total_found": 12
    },
    ...
  ]
}
```

#### c. `/api/evaluation_v3/<query_id>/batch-evaluate` (POST)
Eksperimen batch untuk parameter tuning.

**Request Body:**
```json
{
  "query_text": "puasa",
  "combinations": [
    {
      "w2v_weight": 1.0,
      "ft_weight": 1.0,
      "glove_weight": 1.0,
      "voting_bonus": 0.05,
      "threshold": 0.5,
      "limit": 10
    },
    {
      "w2v_weight": 1.2,
      "ft_weight": 0.8,
      "glove_weight": 1.0,
      "voting_bonus": 0.08,
      "threshold": 0.55,
      "limit": 10
    },
    ...
  ]
}
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "best_combination": {
    "combination_id": 5,
    "parameters": {...},
    "metrics": {
      "precision": 0.88,
      "recall": 0.82,
      "f1": 0.85
    }
  },
  "total_combinations": 25
}
```

## 🎨 Peningkatan UI/UX

### 1. **Animasi dan Transisi**
- Smooth animations untuk panel advanced settings
- Hover effects pada weight sliders
- Animated progress indicators

### 2. **Visual Feedback**
- Real-time weight impact indicators
- Color-coded metric cards
- Winner badges untuk metode terbaik
- Gradient backgrounds untuk highlight

### 3. **Responsive Design**
- Mobile-friendly layout
- Collapsible advanced settings
- Adaptive card layouts

## 📊 Metrik Evaluasi yang Ditingkatkan

Selain metrik standar (Precision, Recall, F1-Score), v3 menambahkan:

1. **Accuracy**: Overall accuracy metric
2. **Execution Time**: Waktu eksekusi per metode
3. **Model Count**: Jumlah model yang menemukan ayat (untuk voting)
4. **Individual Scores**: Skor dari setiap model dasar

## 🔬 Fitur Eksperimental (Future)

Placeholder untuk fitur yang akan datang:
- Threshold sensitivity analysis UI
- Batch parameter tuning interface
- Advanced analytics dashboard
- Export hasil ke berbagai format

## 🚀 Cara Menggunakan

### 1. Akses Halaman
Buka: `http://localhost:5000/evaluasi/v3`

### 2. Tambah Query dan Ayat Relevan
- Sama seperti v2, tambahkan query dan ayat relevan
- Atau import dari Excel

### 3. Konfigurasi Ensemble
- Klik "Pengaturan Ensemble Lanjutan"
- Pilih Quick Preset atau atur manual
- Sesuaikan bobot, threshold, dan parameter lainnya

### 4. Pilih Metode
- Pilih metode yang ingin dievaluasi
- Untuk perbandingan ensemble, pilih metode "Semua (Perbandingan)"

### 5. Jalankan Evaluasi
- Klik "Jalankan Evaluasi"
- Lihat hasil dalam berbagai mode visualisasi

### 6. Analisis Hasil
- Bandingkan metrik antar metode
- Identifikasi konfigurasi terbaik
- Export hasil untuk dokumentasi

## 💡 Tips Penggunaan

1. **Untuk Precision Tinggi**: Gunakan preset "Precision Focus" atau tingkatkan threshold
2. **Untuk Recall Tinggi**: Gunakan preset "Recall Focus" atau turunkan threshold
3. **Untuk Balanced**: Gunakan preset "Balanced" dengan bobot equal
4. **Untuk Eksperimen**: Gunakan metode "Semua" untuk melihat perbandingan lengkap
5. **Untuk Produksi**: Gunakan hasil analisis untuk menentukan konfigurasi optimal

## 🔧 Konfigurasi Backend

### Ensemble Model Configuration
File: `backend/ensemble_embedding.py`

```python
ensemble = EnsembleEmbeddingModel(
    word2vec_model,
    fasttext_model,
    glove_model,
    word2vec_weight=1.2,      # Custom weight
    fasttext_weight=1.0,
    glove_weight=0.8,
    voting_bonus=0.05,        # Bonus for ≥2 models
    use_meta_ensemble=False,  # Use ML-based ensemble
    use_voting_filter=False   # Filter by voting
)
```

## 📈 Perbandingan dengan Versi Sebelumnya

| Fitur | V1 | V2 | V3 |
|-------|----|----|-----|
| Model Selection | ✅ | ✅ | ✅ |
| Threshold Control | ❌ | ✅ | ✅✅ (Per-model) |
| Ensemble Config | ❌ | ❌ | ✅✅ (Full control) |
| Weight Adjustment | ❌ | ❌ | ✅✅ |
| Method Comparison | ❌ | ❌ | ✅✅ |
| Quick Presets | ❌ | ❌ | ✅ |
| Visual Modes | ✅ | ✅ | ✅✅ (3 modes) |
| Batch Experiments | ❌ | ❌ | ✅ (API) |
| Threshold Analysis | ❌ | ❌ | ✅ (API) |

## 🎓 Teori dan Implementasi

### Weighted Averaging
```
Skor = (w1 × s1 + w2 × s2 + w3 × s3) / (w1 + w2 + w3)
```
Hanya model dengan skor > 0 yang dihitung.

### Voting Bonus
```
Skor Akhir = Skor Weighted + Bonus Voting (jika voting ≥2)
```

### Meta-Ensemble
Menggunakan Logistic Regression untuk memprediksi relevansi berdasarkan:
- Skor individual dari setiap model
- Query length
- Verse length
- Model agreement features

## 📝 Catatan Penting

1. **Performance**: Metode "Semua" akan memakan waktu lebih lama karena menjalankan multiple evaluations
2. **Memory**: Batch experiments dengan banyak kombinasi memerlukan memory yang cukup
3. **Threshold**: Nilai threshold yang terlalu tinggi atau rendah dapat menghasilkan hasil yang tidak optimal
4. **Weights**: Bobot 0.0 akan menonaktifkan model dari perhitungan ensemble

## 🐛 Troubleshooting

### Error: "Ayat relevan belum diinput"
**Solusi**: Tambahkan ayat relevan terlebih dahulu untuk query yang dipilih

### Error: "Meta-ensemble model not available"
**Solusi**: Sistem akan fallback ke weighted ensemble secara otomatis

### Hasil evaluasi tidak sesuai ekspektasi
**Solusi**: 
- Coba preset yang berbeda
- Sesuaikan threshold
- Periksa bobot model
- Gunakan mode "Semua" untuk perbandingan

## 🔮 Roadmap

- [ ] UI untuk threshold sensitivity analysis
- [ ] UI untuk batch parameter tuning
- [ ] Export hasil ke Excel/CSV dengan detail lengkap
- [ ] Visualisasi confusion matrix
- [ ] ROC curve dan AUC metrics
- [ ] Saved configurations/profiles
- [ ] History dan comparison antar evaluasi
- [ ] Real-time evaluation progress
- [ ] Advanced statistical analysis

## 📞 Support

Untuk pertanyaan atau masalah, silakan buat issue di repository atau hubungi tim development.

---

**Dibuat dengan ❤️ untuk meningkatkan akurasi evaluasi sistem pencarian semantik Al-Quran**
