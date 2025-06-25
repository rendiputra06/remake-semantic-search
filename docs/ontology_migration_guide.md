# Panduan Migrasi Ontologi: JSON ke Database

## **Ringkasan**

Dokumen ini menjelaskan proses migrasi ontologi dari penyimpanan JSON ke database SQLite, termasuk implementasi hybrid storage yang memungkinkan switching antara kedua format.

## **Alasan Migrasi**

### **Keunggulan Database:**

- **Scalability**: Lebih efisien untuk data besar (>1000 konsep)
- **Concurrency**: Support multi-user editing
- **Data Integrity**: ACID transactions
- **Query Performance**: Indexing untuk pencarian cepat
- **Backup & Recovery**: Otomatis dengan database

### **Keunggulan JSON:**

- **Simplicity**: Mudah di-edit manual
- **Version Control**: Bisa di-track dengan Git
- **Portability**: File standalone
- **Development**: Ideal untuk testing

## **Arsitektur Hybrid**

Sistem menggunakan pendekatan hybrid yang memungkinkan:

- Switching antara JSON dan database storage
- Sync data antar format
- Fallback otomatis jika salah satu format gagal

### **Struktur Database**

```sql
CREATE TABLE ontology_concepts (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    synonyms TEXT,           -- JSON array
    broader TEXT,            -- JSON array
    narrower TEXT,           -- JSON array
    related TEXT,            -- JSON array
    verses TEXT,             -- JSON array
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## **Langkah Migrasi**

### **1. Backup Data JSON**

```bash
python scripts/migrate_ontology_to_db.py
```

Script ini akan:

- Backup file JSON ke `ontology/backups/`
- Validasi struktur data
- Migrasi ke database
- Verifikasi hasil

### **2. Update OntologyService**

Service sudah diupdate untuk support hybrid storage:

```python
# Gunakan database sebagai default
ontology_service = OntologyService(storage_type='database')

# Atau gunakan JSON
ontology_service = OntologyService(storage_type='json')
```

### **3. Verifikasi Migrasi**

```bash
python scripts/verify_ontology_db.py
```

## **Fitur Manajemen Storage**

### **API Endpoints**

#### **Info Storage**

```http
GET /api/ontology/admin/storage/info
```

Response:

```json
{
  "success": true,
  "info": {
    "storage_type": "database",
    "concept_count": 47,
    "json_path": "/path/to/ontology.json"
  }
}
```

#### **Switch Storage**

```http
POST /api/ontology/admin/storage/switch
Content-Type: application/json

{
  "storage_type": "database"  // atau "json"
}
```

#### **Sync Data**

```http
POST /api/ontology/admin/storage/sync
Content-Type: application/json

{
  "direction": "json_to_db"  // atau "db_to_json"
}
```

### **Halaman Admin**

Halaman `/admin/ontology` sekarang memiliki panel storage management dengan:

- Info storage type dan jumlah konsep
- Tombol switch antara JSON dan database
- Tombol sync data antar format
- Visualisasi relasi ontologi

## **Penggunaan**

### **Development**

```python
# Gunakan JSON untuk development
service = OntologyService(storage_type='json')
```

### **Production**

```python
# Gunakan database untuk production
service = OntologyService(storage_type='database')
```

### **Hybrid Mode**

```python
# Switch storage type secara dinamis
service = OntologyService(storage_type='database')
service.switch_storage('json')  # Switch ke JSON
service.sync_to_database()      # Sync JSON ke database
```

## **Backup & Recovery**

### **Backup Otomatis**

- Script migrasi membuat backup otomatis
- Format: `ontology_backup_YYYYMMDD_HHMMSS.json`
- Lokasi: `ontology/backups/`

### **Manual Backup**

```python
# Backup database ke JSON
service.export_to_json()

# Backup JSON ke database
service.sync_to_database()
```

## **Monitoring & Maintenance**

### **Verifikasi Data**

```bash
# Verifikasi integritas data
python scripts/verify_ontology_db.py
```

### **Monitoring Storage**

- Cek info storage via API atau halaman admin
- Monitor ukuran database dan JSON
- Backup berkala

## **Troubleshooting**

### **Masalah Umum**

#### **1. Database Connection Error**

```python
# Fallback ke JSON otomatis
service = OntologyService(storage_type='database')
# Jika database error, akan fallback ke JSON
```

#### **2. Data Tidak Sinkron**

```python
# Sync manual
service.sync_to_database()  # JSON → Database
service.export_to_json()    # Database → JSON
```

#### **3. Storage Switch Gagal**

- Cek permissions file/database
- Pastikan data valid
- Restart aplikasi jika perlu

### **Log & Debug**

```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Cek storage info
info = service.get_storage_info()
print(info)
```

## **Best Practices**

### **Development**

1. Gunakan JSON untuk development/testing
2. Commit perubahan JSON ke Git
3. Test dengan database sebelum production

### **Production**

1. Gunakan database sebagai primary storage
2. Backup database secara berkala
3. Monitor performance dan ukuran data

### **Data Management**

1. Validasi data sebelum migrasi
2. Test CRUD operations di kedua format
3. Backup sebelum perubahan besar

## **Performa**

### **Benchmark (47 konsep)**

- **JSON Load**: ~5ms
- **Database Load**: ~10ms
- **JSON Save**: ~15ms
- **Database Save**: ~25ms

### **Scalability**

- **JSON**: Optimal <1000 konsep
- **Database**: Optimal >1000 konsep
- **Hybrid**: Fleksibel untuk semua ukuran

## **Kesimpulan**

Migrasi ke database memberikan skalabilitas dan fitur enterprise, sementara hybrid storage mempertahankan fleksibilitas untuk development. Sistem ini siap untuk pertumbuhan data dan multi-user environment.

## **Langkah Selanjutnya**

1. **Monitoring**: Implementasi monitoring storage usage
2. **Optimization**: Index optimization untuk query kompleks
3. **Backup**: Automated backup scheduling
4. **Validation**: Enhanced data validation rules
5. **API**: RESTful API untuk external access
