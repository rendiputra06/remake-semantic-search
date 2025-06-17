# Code Refactoring Task List

## 1. Setup Project Structure

- [ ] Buat struktur folder berikut:

```
semantic/
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── decorators.py
│   │   └── models.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── thesaurus/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── search/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config.py
└── main.py
```

## 2. Extract Authentication Logic

- [x] Pindahkan decorator `login_required` dan `admin_required` ke `app/auth/decorators.py`
- [x] Pindahkan route `/login`, `/logout` ke `app/auth/routes.py`
- [x] Pindahkan fungsi autentikasi ke `app/auth/utils.py`

## 3. Extract Admin Features

- [x] Pindahkan route `/admin` ke `app/admin/routes.py`
- [x] Pindahkan fungsi admin tools (wordlist, lexical, thesaurus) ke `app/admin/utils.py`
- [x] Pindahkan route admin API ke `app/admin/routes.py`

## 4. Extract API Routes

- [ ] Pindahkan semua route `/api/*` ke `app/api/routes.py`
- [ ] Buat schema validasi di `app/api/schemas.py`
- [ ] Pisahkan logic API dari route handler

## 5. Extract Thesaurus Features

- [ ] Pindahkan fungsi terkait thesaurus ke `app/thesaurus/utils.py`
- [ ] Pindahkan route visualisasi dan pencarian ke `app/thesaurus/routes.py`

## 6. Extract Search Features

- [ ] Pindahkan route terkait pencarian ke `app/search/routes.py`
- [ ] Pisahkan logic pencarian dari route handler

## 7. Setup Database Models

- [ ] Buat model User di `app/models/user.py`
- [ ] Buat model untuk data lexical/thesaurus

## 8. Configuration Management

- [ ] Pindahkan konfigurasi (secret key, path dll) ke `app/config.py`
- [ ] Buat konfigurasi development dan production

## 9. Create Application Factory

- [ ] Buat factory pattern di `app/__init__.py`
- [ ] Register semua blueprint
- [ ] Setup error handlers

## 10. Setup Main Application

- [ ] Buat `main.py` sebagai entry point
- [ ] Import dan gunakan application factory
- [ ] Setup logging dan error handling

## 11. Testing Setup

- [ ] Buat struktur test untuk setiap modul
- [ ] Setup test fixtures dan helpers
- [ ] Buat unit test untuk fungsi utama

## 12. Documentation

- [ ] Dokumentasi struktur project
- [ ] Dokumentasi API
- [ ] Dokumentasi setup dan deployment

## Priority Order:

1. Setup Project Structure
2. Configuration Management
3. Extract Authentication
4. Setup Database Models
5. Create Application Factory
6. Extract Admin Features
7. Extract API Routes
8. Extract Thesaurus Features
9. Extract Search Features
10. Testing Setup
11. Documentation

## Notes:

- Gunakan blueprint untuk modularisasi
- Terapkan dependency injection
- Pisahkan business logic dari route handlers
- Standardisasi error handling
- Terapkan type hints
- Buat tests bersamaan dengan development
