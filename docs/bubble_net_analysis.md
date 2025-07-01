# Analisis Graph Bubble Net - Pencarian Ontologi

## **Ringkasan**

Graph bubble net adalah visualisasi interaktif yang menampilkan relasi antar konsep hasil pencarian ontologi dalam format bubble/circle network. Visualisasi ini menggantikan graph tradisional dengan pendekatan yang lebih modern dan informatif.

## **Fitur Visualisasi Admin Ontologi**

### **1. Jenis Visualisasi**

#### **Bubble Net (Default)**

- **Layout**: Circular nodes dengan physics engine Barnes-Hut
- **Node Shape**: Circle dengan ukuran dinamis berdasarkan jumlah relasi
- **Edge Style**: Curved dengan arrow untuk menunjukkan arah relasi
- **Color Coding**:
  - Hijau (#28a745) = Broader relationships
  - Kuning (#ffc107) = Narrower relationships
  - Merah (#dc3545) = Related relationships
- **Physics**: Barnes-Hut algorithm dengan gravitational constant -2000

#### **Hierarchical Tree**

- **Layout**: Top-down hierarchical dengan parent-child relationships
- **Node Shape**: Box dengan margin dan padding
- **Edge Style**: Cubic Bezier curves untuk smooth connections
- **Direction**: Up-Down (UD) dengan sort method directed
- **Physics**: Disabled untuk static layout

#### **Force-Directed Graph**

- **Layout**: Force-Atlas2 algorithm untuk distribusi optimal
- **Node Shape**: Dot dengan ukuran fixed 20px
- **Edge Style**: Continuous smooth lines
- **Physics**: Force-Atlas2 dengan gravitational constant -50
- **Spring**: Length 100, constant 0.08

### **2. Filter Relasi**

#### **Filter Options**

- **Broader**: Menampilkan relasi "lebih luas" (parent -> child)
- **Narrower**: Menampilkan relasi "lebih spesifik" (child -> parent)
- **Related**: Menampilkan relasi "terkait" (bidirectional)

#### **Filter Controls**

- Checkbox buttons dengan color coding
- Real-time filter application
- Filter summary dalam toast notification
- Persistence filter state selama session

### **3. Interaktivitas**

#### **Node Interaction**

- **Click**: Buka modal edit konsep
- **Hover**: Highlight node dan connected nodes
- **Tooltip**: Detail konsep (label, sinonim, relasi, ayat)
- **Selection**: Multi-node selection dengan connected edges

#### **Edge Interaction**

- **Hover**: Highlight edge dan connected nodes
- **Label**: Menampilkan jenis relasi (broader/narrower/related)
- **Color**: Inherit dari node dengan opacity
- **Arrow**: Directional arrows untuk hierarchical relationships

#### **View Controls**

- **Zoom**: Mouse wheel untuk zoom in/out
- **Pan**: Drag untuk memindahkan view
- **Reset**: Double click untuk reset view
- **Export**: Download sebagai PNG image

### **4. Statistik Visualisasi**

#### **Real-time Stats**

- **Node Count**: Jumlah konsep yang ditampilkan
- **Edge Count**: Jumlah relasi yang ditampilkan
- **Filter Summary**: Jenis relasi yang aktif
- **Performance**: Update otomatis saat filter berubah

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
- **Interactive Elements**: Zoom, pan, dan selection

### **3. Performance**

- **Efficient Rendering**: Canvas-based rendering
- **Smooth Animation**: 60fps physics simulation
- **Memory Optimized**: DataSet untuk efficient updates

### **4. User Experience**

- **Intuitive Navigation**: Natural mouse interactions
- **Responsive Design**: Works on desktop and tablet
- **Accessibility**: Keyboard navigation support

## **Implementasi Teknis**

### **1. Library Dependencies**

```html
<!-- vis-network CDN -->
<link
  href="https://unpkg.com/vis-network/styles/vis-network.min.css"
  rel="stylesheet"
  type="text/css"
/>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
```

### **2. Data Structure**

```javascript
const data = {
  nodes: new vis.DataSet(nodes),
  edges: new vis.DataSet(edges),
};
```

### **3. Configuration Options**

```javascript
const options = {
  nodes: {
    shape: "circle",
    borderWidth: 2,
    shadow: true,
    font: { size: 12, color: "#ffffff" },
    scaling: { min: 15, max: 35 },
  },
  edges: {
    width: 2,
    shadow: true,
    smooth: { type: "curvedCW", roundness: 0.2 },
  },
  physics: {
    barnesHut: {
      gravitationalConstant: -2000,
      centralGravity: 0.3,
      springLength: 100,
      springConstant: 0.04,
    },
  },
};
```

## **Penggunaan**

### **1. Admin Ontologi**

- **Visualisasi**: Tampilkan relasi antar konsep ontologi
- **Filter**: Pilih jenis relasi yang ingin ditampilkan
- **Edit**: Click node untuk edit konsep
- **Export**: Download visualisasi sebagai gambar

### **2. Pencarian Ontologi**

- **Query Expansion**: Lihat bagaimana query diperluas
- **Result Mapping**: Pahami hubungan query dengan hasil
- **Relevance Scoring**: Visualisasi skor relevansi

## **Best Practices**

### **1. Performance**

- **Limit Node Count**: Optimal <1000 nodes untuk smooth performance
- **Efficient Updates**: Gunakan DataSet untuk batch updates
- **Memory Management**: Destroy network saat tidak digunakan

### **2. User Experience**

- **Loading States**: Tampilkan spinner saat loading
- **Error Handling**: Graceful fallback jika data error
- **Responsive Design**: Adapt layout untuk berbagai screen size

### **3. Accessibility**

- **Keyboard Navigation**: Support tab dan arrow keys
- **Screen Reader**: Proper ARIA labels
- **Color Contrast**: Ensure sufficient contrast ratios

## **Future Enhancements**

### **1. Advanced Features**

- **3D Visualization**: Three.js integration untuk 3D graphs
- **Animation**: Smooth transitions antar layout
- **Clustering**: Auto-clustering untuk large datasets

### **2. Analytics**

- **Usage Tracking**: Monitor user interaction patterns
- **Performance Metrics**: Track rendering performance
- **A/B Testing**: Test different visualization types

### **3. Integration**

- **Real-time Updates**: WebSocket untuk live data
- **Collaborative Editing**: Multi-user editing support
- **API Integration**: External data sources

## **Kesimpulan**

Bubble net visualization memberikan cara yang intuitif dan informatif untuk memahami relasi kompleks dalam ontologi. Dengan fitur filter, multiple layout types, dan interaktivitas yang kaya, visualisasi ini memungkinkan user untuk mengeksplorasi data ontologi dengan cara yang efisien dan engaging.

Implementasi di admin ontologi menunjukkan bagaimana visualisasi dapat digunakan untuk manajemen data yang efektif, sementara integrasi dengan pencarian ontologi memperkaya pengalaman pencarian dengan pemahaman relasi konseptual.
