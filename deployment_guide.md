# Panduan Deployment Aplikasi Pencarian Semantik Al-Quran

Dokumen ini berisi panduan langkah-demi-langkah untuk men-deploy aplikasi Pencarian Semantik Al-Quran pada server Linux dengan menggunakan Gunicorn sebagai server aplikasi WSGI dan Nginx sebagai reverse proxy.

## Persyaratan

- Server Linux (Ubuntu 20.04 LTS atau lebih baru direkomendasikan)
- Python 3.8 atau lebih baru
- pip
- virtualenv atau venv
- Nginx
- Git

## 1. Persiapan Server

### 1.1 Update dan Upgrade Sistem

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Instal Dependensi Sistem

```bash
sudo apt install -y python3 python3-pip python3-venv nginx git sqlite3 build-essential python3-dev
```

## 2. Clone Repository dari Git

```bash
# Buat direktori aplikasi
mkdir -p /var/www/quran-semantic
cd /var/www/quran-semantic

# Clone repository
git clone https://github.com/username/quran-semantic-search.git .

# Atur izin
sudo chown -R $USER:$USER /var/www/quran-semantic
```

## 3. Persiapkan Lingkungan Virtual Python

```bash
# Buat lingkungan virtual
python3 -m venv venv

# Aktifkan lingkungan virtual
source venv/bin/activate

# Instal dependensi aplikasi
pip install -r requirements.txt

# Instal Gunicorn
pip install gunicorn
```

## 4. Konfigurasi Aplikasi

### 4.1 Periksa Konfigurasi Database

Pastikan path database sudah benar di file `backend/db.py`:

```python
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database/app.db')
```

### 4.2 Inisialisasi Database

```bash
# Buat direktori database jika belum ada
mkdir -p database

# Inisialisasi database
python -c "from backend.db import init_db; init_db()"
```

### 4.3 Konfigurasi File .env (Opsional)

Buat file `.env` untuk menyimpan konfigurasi sensitif (jika dibutuhkan):

```bash
touch .env
```

Tambahkan konfigurasi seperti:

```
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=your_domain.com,www.your_domain.com
```

## 5. Konfigurasi Gunicorn

### 5.1 Buat File Systemd Service

Buat file `/etc/systemd/system/quran-semantic.service`:

```bash
sudo nano /etc/systemd/system/quran-semantic.service
```

Isi dengan konfigurasi berikut:

```ini
[Unit]
Description=Gunicorn daemon untuk Aplikasi Pencarian Semantik Al-Quran
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/quran-semantic
ExecStart=/var/www/quran-semantic/venv/bin/gunicorn --config gunicorn_config.py wsgi:app

[Install]
WantedBy=multi-user.target
```

### 5.2 Buat File konfigurasi Gunicorn

Buat file `gunicorn_config.py` di direktori root aplikasi:

```bash
nano /var/www/quran-semantic/gunicorn_config.py
```

Isi dengan konfigurasi berikut:

```python
bind = "unix:/var/www/quran-semantic/quran_semantic.sock"
workers = 3
timeout = 120
worker_class = "sync"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
```

Buat direktori untuk log:

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown -R www-data:www-data /var/log/gunicorn
```

## 6. Konfigurasi Nginx sebagai Reverse Proxy

### 6.1 Buat Konfigurasi Nginx

```bash
sudo nano /etc/nginx/sites-available/quran-semantic
```

Isi dengan konfigurasi berikut:

```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/quran-semantic/quran_semantic.sock;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias /var/www/quran-semantic/static/;
    }

    location /models/ {
        deny all;
        return 404;
    }

    location /database/ {
        deny all;
        return 404;
    }
}
```

### 6.2 Aktifkan Konfigurasi Nginx

```bash
sudo ln -s /etc/nginx/sites-available/quran-semantic /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Atur Izin File dan Direktori

```bash
sudo chown -R www-data:www-data /var/www/quran-semantic
chmod -R 755 /var/www/quran-semantic
```

## 8. Mulai Layanan Gunicorn

```bash
sudo systemctl start quran-semantic
sudo systemctl enable quran-semantic
```

## 9. Konfigurasi SSL dengan Certbot (Opsional tetapi Direkomendasikan)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

## 10. Optimasi Performa (Opsional)

### 10.1 Konfigurasi Sysctl

```bash
sudo nano /etc/sysctl.conf
```

Tambahkan atau modifikasi baris-baris berikut:

```
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fin_timeout = 15
```

Terapkan perubahan:

```bash
sudo sysctl -p
```

### 10.2 Konfigurasi Ulang Worker Gunicorn

Untuk server dengan spesifikasi tinggi, Anda dapat menyesuaikan jumlah worker Gunicorn:

```bash
# Rumus umum: (2 x jumlah_core) + 1
```

Ubah nilai `workers` di file `gunicorn_config.py` sesuai dengan spesifikasi server Anda.

## 11. Pemeliharaan

### 11.1 Memantau Log

```bash
# Log Gunicorn
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/gunicorn/access.log

# Log Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 11.2 Restart Layanan

```bash
# Restart Gunicorn
sudo systemctl restart quran-semantic

# Restart Nginx
sudo systemctl restart nginx
```

### 11.3 Update Aplikasi

```bash
cd /var/www/quran-semantic
sudo -u www-data git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart quran-semantic
```

## 12. Troubleshooting

### 12.1 Cek Status Layanan

```bash
sudo systemctl status quran-semantic
sudo systemctl status nginx
```

### 12.2 Cek Koneksi Socket

```bash
ls -la /var/www/quran-semantic/quran_semantic.sock
```

### 12.3 Periksa Izin

```bash
sudo namei -l /var/www/quran-semantic/quran_semantic.sock
```

### 12.4 Uji Konfigurasi Nginx

```bash
sudo nginx -t
```

## Catatan Penting

1. Selalu ganti `your_domain.com` dengan domain sebenarnya.
2. Pastikan untuk mengganti `username/quran-semantic-search` dengan URL repository Git yang benar.
3. Jika aplikasi menggunakan model machine learning yang besar, pastikan server memiliki RAM yang cukup.
4. Pastikan untuk membuat backup database secara berkala.
5. Untuk aplikasi ini, file vektor model perlu diinisialisasi juga, pastikan direktori untuk menyimpan vektor tersebut sudah ada dan dapat diakses.

## Inisialisasi Model Word2Vec

Pastikan model Word2Vec diinisialisasi sebelum menjalankan aplikasi:

```bash
# Buat direktori untuk menyimpan vektor
mkdir -p database/vectors

# Aktifkan lingkungan virtual
source venv/bin/activate

# Jalankan script inisialisasi
python -c "from backend.api import init_model; init_model('word2vec')"
```

---

Untuk informasi lebih lanjut atau bantuan, hubungi tim dukungan teknis.
