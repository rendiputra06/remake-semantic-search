# Halaman Informasi Pencarian Ontologi

## Overview

Halaman Informasi Pencarian Ontologi adalah halaman edukatif yang memberikan penjelasan lengkap tentang sistem pencarian ontologi yang telah dikembangkan. Halaman ini dirancang untuk membantu pengguna memahami konsep, proses, dan manfaat dari pencarian ontologi dalam konteks Al-Quran.

## Fitur Utama

### 1. Navigation Tabs

Halaman menggunakan sistem tab untuk mengorganisir informasi:

- **Overview**: Penjelasan umum tentang pencarian ontologi
- **Ontologi**: Struktur dan komponen ontologi
- **Pencarian**: Proses dan alur pencarian ontologi
- **Visualisasi**: Penjelasan tentang visualisasi bubble net
- **Contoh**: Contoh penggunaan dan perbandingan

### 2. Konten Informatif

#### Overview Tab

- Definisi pencarian ontologi
- Tujuan dan manfaat
- Keunggulan sistem (Pemahaman Semantik, Ekspansi Query, Akurasi Tinggi)

#### Ontologi Tab

- Tabel komponen ontologi (Konsep, Label, Sinonim, Broader, Narrower, Related, Ayat)
- Diagram relasi hierarkis
- Contoh konsep ontologi (Iman, Ilmu)

#### Search Tab

- Timeline alur pencarian (5 tahap)
- Teknik ekspansi query (Sinonim, Broader, Related)
- Sistem scoring dan ranking

#### Visualization Tab

- Komponen visualisasi bubble net
- Interaktivitas (Hover, Zoom, Pan)
- Keunggulan visualisasi

#### Examples Tab

- Contoh pencarian "Iman" dan "Ilmu"
- Perbandingan pencarian tradisional vs ontologi
- Tips penggunaan

### 3. Call to Action

Tombol untuk langsung mencoba pencarian ontologi dengan link ke halaman pencarian.

## Struktur File

```
templates/
└── ontology_info.html          # Template halaman informasi ontologi

run.py                          # Route: /ontology-info
```

## Route

```python
@app.route('/ontology-info')
def ontology_info():
    """Halaman informasi detail tentang pencarian ontologi."""
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return render_template('ontology_info.html', user=user)
```

## Navigasi

Menu "Informasi Ontologi" ditambahkan ke dropdown "Informasi" di navbar:

```html
<li>
  <a class="dropdown-item" href="{{ url_for('ontology_info') }}">
    <i class="fas fa-brain me-2"></i>Informasi Ontologi
  </a>
</li>
```

## Styling

### Timeline CSS

```css
.timeline {
  position: relative;
  padding-left: 30px;
}

.timeline::before {
  content: "";
  position: absolute;
  left: 15px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #dee2e6;
}

.timeline-item {
  position: relative;
  margin-bottom: 30px;
}

.timeline-marker {
  position: absolute;
  left: -22px;
  top: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.timeline-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
  border-left: 3px solid #007bff;
}
```

## Komponen Visual

### 1. Header

- Judul dengan ikon otak
- Deskripsi singkat
- Layout responsif

### 2. Tab Navigation

- Bootstrap tabs dengan ikon
- 5 tab utama
- Transisi smooth

### 3. Content Cards

- Card-based layout
- Color-coded sections
- Responsive grid system

### 4. Interactive Elements

- Hover effects
- Color-coded badges
- Alert boxes untuk highlight

## Responsivitas

- **Desktop**: Layout 2-3 kolom
- **Tablet**: Layout 2 kolom
- **Mobile**: Layout 1 kolom dengan stacking

## Aksesibilitas

- Semantic HTML structure
- ARIA labels untuk tabs
- Color contrast yang baik
- Keyboard navigation support

## Integrasi

### 1. Dengan Sistem Pencarian

- Link langsung ke halaman pencarian ontologi
- Contoh query yang bisa dicoba
- Penjelasan hasil pencarian

### 2. Dengan Visualisasi

- Penjelasan bubble net
- Komponen visualisasi
- Interaktivitas

### 3. Dengan Ontologi

- Referensi ke konsep ontologi
- Contoh struktur data
- Relasi hierarkis

## Manfaat

### 1. Edukasi Pengguna

- Memahami konsep ontologi
- Mengetahui proses pencarian
- Memahami visualisasi

### 2. Peningkatan UX

- Informasi yang terorganisir
- Navigasi yang mudah
- Visual yang menarik

### 3. Dokumentasi

- Referensi untuk pengguna
- Penjelasan teknis
- Contoh penggunaan

## Pengembangan Masa Depan

### 1. Interaktif Demo

- Demo langsung pencarian
- Simulasi proses
- Contoh hasil real-time

### 2. Video Tutorial

- Screencast penggunaan
- Penjelasan visual
- Step-by-step guide

### 3. FAQ Section

- Pertanyaan umum
- Troubleshooting
- Best practices

### 4. Feedback System

- Rating halaman
- Saran perbaikan
- Report issues

## Testing

### 1. Functional Testing

- [ ] Semua tab berfungsi
- [ ] Link navigasi bekerja
- [ ] Responsivitas di berbagai device

### 2. Content Testing

- [ ] Informasi akurat
- [ ] Contoh relevan
- [ ] Penjelasan jelas

### 3. UX Testing

- [ ] Kemudahan navigasi
- [ ] Kecepatan loading
- [ ] Accessibility compliance

## Maintenance

### 1. Content Updates

- Update contoh sesuai data ontologi terbaru
- Refresh statistik dan metrics
- Update screenshots jika ada perubahan UI

### 2. Technical Maintenance

- Update dependencies
- Optimize performance
- Fix bugs dan issues

### 3. User Feedback

- Monitor user feedback
- Implement improvements
- Track usage analytics
