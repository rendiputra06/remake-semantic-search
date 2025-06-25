# Analisis Graph Bubble Net - Pencarian Ontologi

## **Ringkasan**

Graph bubble net adalah visualisasi interaktif yang menampilkan relasi antar konsep hasil pencarian ontologi dalam format bubble/circle network. Visualisasi ini menggantikan graph tradisional dengan pendekatan yang lebih modern dan informatif.

## **Arsitektur Visualisasi**

### **1. Struktur Node (Bubble)**

#### **Node Utama (Main Query)**

- **Posisi**: Center/tengah graph
- **Ukuran**: 30px (terbesar)
- **Warna**: Biru (#007bff)
- **Fungsi**: Menunjukkan kata kunci utama pencarian
- **Label**: Kata kunci yang dimasukkan user

#### **Node Ekspansi (Expanded Queries)**

- **Posisi**: Mengelilingi node utama
- **Ukuran**: 20px (sedang)
- **Warna**: Hijau (#28a745)
- **Fungsi**: Menunjukkan kata-kata hasil ekspansi ontologi
- **Label**: Sinonim, related terms, broader/narrower concepts

#### **Node Hasil (Result Verses)**

- **Posisi**: Di luar node ekspansi
- **Ukuran**: 15-25px (dinamis berdasarkan skor)
- **Warna**:
  - Kuning (#ffc107) untuk hasil boosted
  - Abu-abu (#6c757d) untuk hasil normal
- **Fungsi**: Menunjukkan ayat-ayat hasil pencarian
- **Label**: Q.S. [surah]:[ayat]

### **2. Struktur Edge (Koneksi)**

#### **Koneksi Utama → Ekspansi**

- **Warna**: Hijau (#28a745)
- **Ketebalan**: 2px
- **Tipe**: Curved CW dengan roundness 0.2
- **Fungsi**: Menunjukkan relasi ekspansi dari query utama

#### **Koneksi Ekspansi → Hasil**

- **Warna**: Abu-abu (#6c757d)
- **Ketebalan**: 1px
- **Tipe**: Curved CW dengan roundness 0.1
- **Fungsi**: Menunjukkan hasil pencarian dari ekspansi tertentu

#### **Koneksi Utama → Hasil**

- **Warna**: Biru (#007bff)
- **Ketebalan**: 2px
- **Tipe**: Curved CW dengan roundness 0.1
- **Fungsi**: Menunjukkan hasil langsung dari query utama

## **Algoritma Layout**

### **Physics Engine: Barnes-Hut**

```javascript
physics: {
  barnesHut: {
    gravitationalConstant: -2000,  // Gaya gravitasi antar node
    centralGravity: 0.3,           // Gaya gravitasi ke pusat
    springLength: 95,              // Panjang ideal spring
    springConstant: 0.04,          // Kekuatan spring
    damping: 0.09                  // Redaman gerakan
  }
}
```

### **Layout Strategy**

1. **Node utama** ditempatkan di pusat
2. **Node ekspansi** mengelilingi node utama dengan jarak optimal
3. **Node hasil** ditempatkan di luar berdasarkan koneksi
4. **Physics engine** mengatur posisi final secara otomatis

## **Interaktivitas**

### **Hover Effects**

- **Tooltip**: Menampilkan detail node saat hover
- **Delay**: 200ms untuk menghindari flickering
- **Content**: Nama surah, skor, dan terjemahan

### **Zoom & Pan**

- **Zoom**: Mouse wheel untuk zoom in/out
- **Pan**: Drag untuk memindahkan view
- **Reset**: Double click untuk reset view

### **Node Interaction**

- **Click**: Focus pada node tertentu
- **Drag**: Memindahkan posisi node
- **Selection**: Highlight node yang dipilih

## **Analisis Data Flow**

### **1. Query Processing**

```
User Input → Ontology Expansion → Multiple Searches → Results Aggregation
```

### **2. Visual Mapping**

```
Main Query → Blue Center Node
Expanded Terms → Green Middle Nodes
Search Results → Yellow/Gray Outer Nodes
```

### **3. Relationship Visualization**

```
Query → Expansion: Thick green edges
Expansion → Results: Thin gray edges
Query → Direct Results: Thick blue edges
```

## **Keunggulan Bubble Net**

### **1. Visual Clarity**

- **Hierarchical Layout**: Struktur data yang jelas
- **Color Coding**: Membedakan jenis node dengan mudah
- **Size Variation**: Skor relevansi terlihat dari ukuran

### **2. Information Density**

- **Compact Display**: Banyak informasi dalam ruang kecil
- **Contextual Tooltips**: Detail tanpa mengganggu layout
- **Dynamic Sizing**: Ukuran node mencerminkan importance

### **3. User Experience**

- **Intuitive Navigation**: Zoom, pan, hover yang natural
- **Quick Understanding**: Struktur relasi mudah dipahami
- **Interactive Feedback**: Responsif terhadap user action

## **Perbandingan dengan Graph Tradisional**

| Aspek             | Graph Tradisional | Bubble Net             |
| ----------------- | ----------------- | ---------------------- |
| **Layout**        | Hierarchical tree | Force-directed network |
| **Node Shape**    | Rectangle/Box     | Circle/Bubble          |
| **Edge Style**    | Straight lines    | Curved lines           |
| **Information**   | Text-heavy        | Visual-focused         |
| **Interactivity** | Limited           | Rich                   |
| **Scalability**   | Good              | Excellent              |

## **Optimasi Performa**

### **1. Node Limit**

- **Maksimal**: 50 node untuk performa optimal
- **Threshold**: Warning jika >100 node
- **Clustering**: Grouping untuk data besar

### **2. Rendering Optimization**

- **Canvas Rendering**: Hardware acceleration
- **Lazy Loading**: Load data on demand
- **Caching**: Cache layout calculations

### **3. Memory Management**

- **Garbage Collection**: Cleanup unused objects
- **Event Cleanup**: Remove listeners saat destroy
- **Data Structure**: Efficient data representation

## **Use Cases**

### **1. Semantic Search Analysis**

- **Input**: Kata kunci pencarian
- **Output**: Visualisasi ekspansi dan hasil
- **Benefit**: Memahami proses ekspansi ontologi

### **2. Query Optimization**

- **Input**: Multiple search queries
- **Output**: Comparison of expansion strategies
- **Benefit**: Optimasi algoritma ekspansi

### **3. Result Analysis**

- **Input**: Search results dengan metadata
- **Output**: Pattern recognition dalam hasil
- **Benefit**: Identifikasi bias atau gap dalam data

## **Future Enhancements**

### **1. Advanced Filtering**

- **Score-based**: Filter berdasarkan skor relevansi
- **Source-based**: Filter berdasarkan sumber query
- **Category-based**: Filter berdasarkan kategori konsep

### **2. Animation Features**

- **Loading Animation**: Smooth transition saat load
- **Update Animation**: Animate perubahan data
- **Focus Animation**: Highlight path ke node tertentu

### **3. Export Capabilities**

- **Image Export**: Export sebagai PNG/SVG
- **Data Export**: Export data graph
- **Report Generation**: Generate analisis report

## **Metrics & Analytics**

### **1. User Interaction**

- **Hover Frequency**: Seberapa sering user hover
- **Zoom Level**: Preferred zoom range
- **Node Clicks**: Most clicked nodes

### **2. Performance Metrics**

- **Render Time**: Waktu rendering graph
- **Memory Usage**: Penggunaan memory
- **Frame Rate**: Smoothness of interaction

### **3. Data Insights**

- **Popular Queries**: Query yang sering digunakan
- **Expansion Patterns**: Pola ekspansi yang efektif
- **Result Distribution**: Distribusi skor hasil

## **Kesimpulan**

Bubble net graph memberikan visualisasi yang lebih modern, interaktif, dan informatif dibanding graph tradisional. Dengan layout force-directed, color coding yang jelas, dan interaktivitas yang kaya, user dapat dengan mudah memahami relasi kompleks dalam hasil pencarian ontologi.

Visualisasi ini tidak hanya menampilkan data, tetapi juga membantu user memahami proses dan hasil pencarian semantik dengan ontologi secara visual yang intuitif.
