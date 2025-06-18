# Changelog - Perubahan dari app.py ke run.py

## Versi 2.0.0 - 2025-06-17

### Perubahan Utama

- **Renamed**: `app.py` → `run.py` untuk menghindari konflik dengan folder `app/`
- **Fixed**: Error Gunicorn "Failed to find attribute 'app' in 'app'"

### File yang Diubah

#### 1. **run.py** (sebelumnya app.py)

- File utama aplikasi Flask tetap sama
- Hanya nama file yang berubah

#### 2. **wsgi.py**

```python
# Sebelum
from app import app

# Sesudah
from run import app
```

#### 3. **Dockerfile** (Production)

```dockerfile
# Sebelum
ENV FLASK_APP=app.py

# Sesudah
ENV FLASK_APP=run.py
```

#### 4. **Dockerfile.dev** (Development)

```dockerfile
# Sebelum
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Sesudah
ENV FLASK_APP=run.py
ENV FLASK_DEBUG=1
# ENV FLASK_ENV=development  # Dihapus karena deprecated
```

#### 5. **docker-compose.yml** (Production)

```yaml
# Sebelum
ports:
  - "7000:7000"
environment:
  - FLASK_ENV=production

# Sesudah
ports:
  - "5000:5000"
environment:
  - FLASK_DEBUG=0
```

#### 6. **docker-compose.dev.yml** (Development)

```yaml
# Sebelum
environment:
  - FLASK_ENV=development
  - FLASK_DEBUG=1
command: ["python", "app.py"]

# Sesudah
environment:
  - FLASK_APP=run.py
  - FLASK_DEBUG=1
  - PYTHONUNBUFFERED=1
command: ["python", "run.py"]
```

#### 7. **README.md**

- Updated semua referensi dari `app.py` ke `run.py`
- Updated struktur proyek
- Updated perintah instalasi manual

### Cara Menjalankan

#### Development Mode

```bash
docker-compose -f docker-compose.dev.yml up --build
```

#### Production Mode

```bash
docker-compose up --build
```

#### Manual Installation

```bash
python run.py
```

### Troubleshooting

#### Error: "Failed to find attribute 'app' in 'app'"

- **Penyebab**: Konflik nama antara file `app.py` dan folder `app/`
- **Solusi**: Gunakan `run.py` sebagai nama file utama

#### Error: "FLASK_ENV is deprecated"

- **Penyebab**: Flask 2.3+ tidak lagi mendukung `FLASK_ENV`
- **Solusi**: Gunakan `FLASK_DEBUG=1` untuk development, `FLASK_DEBUG=0` untuk production

#### Error: "ImportError: cannot import name 'app' from 'app'"

- **Penyebab**: Gunicorn mencoba import dari folder `app/` bukan file `app.py`
- **Solusi**: Gunakan `wsgi:app` sebagai entry point Gunicorn

### Keuntungan Perubahan

1. **Menghindari Konflik Nama**: Tidak ada lagi konflik antara file dan folder
2. **Compatibility**: Sesuai dengan Flask 2.3+
3. **Clarity**: Nama `run.py` lebih jelas menunjukkan file utama
4. **Stability**: Gunicorn dapat menemukan aplikasi dengan benar
