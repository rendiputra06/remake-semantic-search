# 🔍 Dokumentasi Lengkap - Search Processes & Routes

Dokumentasi khusus untuk semua proses pencarian dalam aplikasi Semantic Search Engine, meliputi **Lexical Search**, **Semantic Search**, dan **Ontology Search**.

## 🏗️ Overview Arsitektur Search

Aplikasi ini menyediakan 3 jenis pencarian utama:

- **🔤 Lexical Search** - Pencarian berbasis kata kunci tradisional
- **🧠 Semantic Search** - Pencarian berbasis makna menggunakan model embedding
- **🕸️ Ontology Search** - Pencarian dengan ekspansi konsep ontologi

## 🚀 Search API Routes

### **📍 Base URL untuk Search:**
- **Development**: `http://localhost:5000/api/search`
- **Blueprint**: `search_bp` (didaftarkan di `app/api/routes/__init__.py`)

---

## 🔤 Lexical Search Routes

### **1. Basic Lexical Search**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/search/lexical` | POST | Pencarian leksikal dasar | `app/api/routes/search.py:140` | ❌ |

**Request Body:**
```json
{
  "query": "apa arti sabar",
  "exact_match": false,
  "use_regex": false,
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "apa arti sabar",
    "search_type": "lexical",
    "exact_match": false,
    "use_regex": false,
    "results": [...],
    "count": 5
  }
}
```

**Fitur:**
- ✅ Pencarian berbasis kata kunci
- ✅ Support exact match & regex
- ✅ Limit hasil pencarian
- ✅ Integrasi dengan search history

---

## 🧠 Semantic Search Routes

### **1. Basic Semantic Search**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/search` | POST | Pencarian semantik dasar | `app/api/routes/search.py:36` | ❌ |

**Request Body:**
```json
{
  "query": "apa arti kesabaran",
  "model": "word2vec",
  "limit": 10,
  "threshold": 0.5,
  "aggregation_method": null,
  "vector_file": null
}
```

**Supported Models:**
- `word2vec` - Word2Vec embedding model
- `fasttext` - FastText embedding model
- `glove` - GloVe embedding model
- `ensemble` - Ensemble dari multiple models

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "apa arti kesabaran",
    "model": "word2vec",
    "threshold": 0.5,
    "execution_time": 0.1234,
    "results": [
      {
        "verse_id": 123,
        "surah": 2,
        "ayah": 255,
        "text": "...",
        "similarity": 0.87,
        "rank": 1
      }
    ],
    "count": 1
  }
}
```

**Fitur:**
- ✅ Multiple embedding models
- ✅ Configurable threshold & limit
- ✅ Execution time tracking
- ✅ User settings integration

### **2. Expanded Search (Query Expansion)**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/search/expanded` | POST | Pencarian dengan ekspansi sinonim | `app/api/routes/search.py:198` | ❌ |

**Request Body:**
```json
{
  "query": "kesabaran",
  "model": "word2vec",
  "limit": 15,
  "threshold": 0.6
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "kesabaran",
    "model": "word2vec",
    "search_type": "expanded",
    "expanded_queries": ["kesabaran", "sabar", "tabah"],
    "results": [...],
    "count": 8
  }
}
```

**Fitur:**
- ✅ Query expansion menggunakan thesaurus
- ✅ Multiple query execution
- ✅ Duplicate removal & result ranking
- ✅ Classification enhancement

### **3. Search Distribution Analysis**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/search/distribution` | POST | Analisis distribusi hasil pencarian | `app/api/routes/search.py:318` | ❌ |

---

## 🕸️ Ontology Search Routes

### **📍 Base URL untuk Ontology:**
- **Development**: `http://localhost:5000/api/ontology`
- **Blueprint**: `ontology_bp` (didaftarkan di `run.py`)

### **1. Ontology-Enhanced Search**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/ontology/search` | POST | Pencarian dengan ekspansi ontologi | `app/api/routes/ontology.py:90` | ❌ |

**Request Body:**
```json
{
  "query": "kesabaran",
  "model": "word2vec",
  "limit": 10,
  "threshold": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "query": "kesabaran",
  "expanded_queries": ["kesabaran", "sabar", "tabah", "istiqomah"],
  "results": [...],
  "bubble_net": [...],
  "count": 8
}
```

**Fitur:**
- ✅ Ontology concept expansion
- ✅ Multiple query search execution
- ✅ Similarity boosting for ontology matches
- ✅ Bubble net data for visualization

### **2. Ontology Tracing (Debug Mode)**

| Route | Method | Description | Location | Authentication |
|-------|---------|-------------|----------|---------------|
| `/api/ontology/trace` | POST | Tracing lengkap proses ontologi | `app/api/routes/ontology.py:336` | ❌ |

**Response:**
```json
{
  "success": true,
  "trace": {
    "query": "kesabaran",
    "steps": [
      {
        "step": "ontology_expansion",
        "data": {...},
        "duration_ms": 45.2,
        "logs": [...]
      },
      {
        "step": "semantic_search",
        "data": [...],
        "duration_ms": 123.5,
        "logs": [...]
      },
      {
        "step": "boosting_ranking",
        "data": [...],
        "duration_ms": 12.3,
        "logs": [...]
      }
    ],
    "statistics": {
      "total_queries": 4,
      "total_initial_results": 25,
      "boosted_results": 8,
      "final_results": 10
    }
  }
}
```

**Fitur:**
- ✅ Step-by-step process tracing
- ✅ Performance metrics
- ✅ Detailed logging
- ✅ Statistics breakdown

---

## 🔧 Search Service Integration

### **Backend Services:**

#### **1. SearchService Class**
- **Location**: `app/api/services/search_service.py`
- **Methods**:
  - `semantic_search()` - Core semantic search
  - `_init_semantic_model()` - Model initialization
  - `_enhance_results_with_classification()` - Result enhancement

#### **2. LexicalSearch Class**
- **Location**: `backend/lexical_search.py`
- **Methods**:
  - `load_index()` - Load search index
  - `search()` - Execute lexical search

#### **3. IndonesianThesaurus Class**
- **Location**: `backend/thesaurus.py`
- **Methods**:
  - `get_synonyms()` - Get word synonyms
  - Query expansion support

#### **4. OntologyService Class**
- **Location**: `app/api/services/ontology_service.py`
- **Methods**:
  - `find_concept()` - Find ontology concepts
  - `get_related()` - Get related concepts
  - `add_concept()` - Add new concepts

---

## 📊 Supported Models & Algorithms

### **Embedding Models:**
| Model | Description | Location |
|-------|-------------|----------|
| **Word2Vec** | Google Word2Vec pre-trained | `models/` |
| **FastText** | Facebook FastText | `models/` |
| **GloVe** | Stanford GloVe | `models/` |
| **Ensemble** | Combined model results | Service layer |

### **Search Algorithms:**
1. **Cosine Similarity** - Vector similarity calculation
2. **TF-IDF** - Lexical search scoring
3. **Ontology Expansion** - Concept relationship traversal
4. **Query Expansion** - Synonym-based query broadening

---

## 🔐 Authentication & Security

### **Search Endpoints Security:**

| Endpoint | Authentication | Rate Limiting | Logging |
|----------|---------------|---------------|---------|
| `/api/search` | ❌ | ❌ | ✅ |
| `/api/search/lexical` | ❌ | ❌ | ✅ |
| `/api/search/expanded` | ❌ | ❌ | ✅ |
| `/api/ontology/search` | ❌ | ❌ | ✅ |
| `/api/ontology/trace` | ❌ | ❌ | ✅ |

**Note**: Semua search endpoints bersifat publik untuk memudahkan akses pengguna.

---

## 📈 Performance & Monitoring

### **Metrics yang Dicatat:**
- ✅ **Execution Time** - Waktu eksekusi setiap search
- ✅ **Result Count** - Jumlah hasil yang dikembalikan
- ✅ **Model Usage** - Model mana yang digunakan
- ✅ **User Statistics** - Jika user login

### **Search History:**
- ✅ Otomatis dicatat untuk user yang login
- ✅ Menyimpan query, model, dan jumlah hasil
- ✅ Accessible via admin panel

---

## 🚀 Usage Examples

### **Basic Semantic Search:**
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "apa arti kesabaran",
    "model": "word2vec",
    "limit": 10
  }'
```

### **Lexical Search:**
```bash
curl -X POST http://localhost:5000/api/search/lexical \
  -H "Content-Type: application/json" \
  -d '{
    "query": "kesabaran",
    "exact_match": false,
    "limit": 5
  }'
```

### **Ontology-Enhanced Search:**
```bash
curl -X POST http://localhost:5000/api/ontology/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "kesabaran",
    "model": "ensemble",
    "limit": 15
  }'
```

### **Debug Tracing:**
```bash
curl -X POST http://localhost:5000/api/ontology/trace \
  -H "Content-Type: application/json" \
  -d '{
    "query": "kesabaran",
    "model": "word2vec"
  }'
```

---

## 🔧 Configuration Parameters

### **Search Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | - | **Required** - Query pencarian |
| `model` | string | `"word2vec"` | Model embedding yang digunakan |
| `limit` | integer | `10` | Maksimal jumlah hasil |
| `threshold` | float | `0.5` | Minimum similarity score |
| `exact_match` | boolean | `false` | Lexical search exact match |
| `use_regex` | boolean | `false` | Lexical search regex mode |

### **Model-Specific Parameters:**
- **aggregation_method** - Untuk ensemble models
- **vector_file** - Custom vector file path

---

## 🎯 Search Flow Architecture

```
User Query → Route Handler → Service Layer → Backend Models
     ↓           ↓             ↓              ↓
   Input    → Validation → Search Logic → Model Execution
     ↓           ↓             ↓              ↓
   Process → Parameters → Algorithm → Results
     ↓           ↓             ↓              ↓
   Format → Enhancement → Ranking → Response
```

**Flow Details:**
1. **Input Validation** - Parameter checking & sanitization
2. **Model Selection** - Choose appropriate embedding model
3. **Query Processing** - Text preprocessing & tokenization
4. **Vector Generation** - Convert query to vector representation
5. **Similarity Calculation** - Compare with document vectors
6. **Result Enhancement** - Add metadata & classification
7. **Ranking & Filtering** - Sort by relevance & apply limits

---

## 📚 Related Files & Components

### **Core Search Files:**
- `app/api/routes/search.py` - Main search endpoints
- `app/api/routes/ontology.py` - Ontology search endpoints
- `app/api/services/search_service.py` - Search service logic
- `backend/lexical_search.py` - Lexical search engine
- `backend/thesaurus.py` - Thesaurus functionality

### **Model Files:**
- `models/` - Directory containing embedding models
- `backend/semantic_search.py` - Semantic search implementation

### **Database Integration:**
- `backend/db.py` - Database connection & queries
- Search history & user preferences storage

---

## 🔄 Recent Updates & Improvements

- ✅ **Multi-Model Support** - Word2Vec, FastText, GloVe, Ensemble
- ✅ **Ontology Integration** - Concept expansion & boosting
- ✅ **Query Expansion** - Synonym-based search broadening
- ✅ **Performance Tracing** - Detailed execution monitoring
- ✅ **Result Enhancement** - Classification & metadata addition

---

*Generated on: 2025-10-09* | *Search Routes Documented: 7*
