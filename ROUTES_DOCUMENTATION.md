## 🏗️ Struktur Aplikasi

Aplikasi ini menggunakan **Flask** dengan struktur blueprint untuk mengorganisir routes:

- **Main Routes** (`run.py`) - Routes utama aplikasi
- **Admin Blueprint** (`app/admin/routes.py`) - Routes untuk administrasi sistem
- **Auth Blueprint** (`app/auth/routes.py`) - Routes untuk autentikasi pengguna
- **API Routes** (`app/api/routes.py`) - REST API endpoints
- **Query Blueprint** (`app/api/routes/query.py`) - Routes untuk query management
- **Public Blueprint** (`app/public.py`) - Routes publik

### 📁 Struktur Template Admin (Modular)

Template admin sekarang menggunakan struktur modular untuk kemudahan maintenance:

```
templates/admin/
├── layout.html              # Layout utama dengan styling modern
├── tabs.html               # Komponen navigasi tab
├── modals.html             # Modal untuk berbagai aksi admin
├── users/
│   └── management.html     # Tab manajemen user
├── models/
│   └── status.html         # Tab status model AI
├── linguistic/
│   ├── main.html          # Container utama linguistic
│   ├── lexical.html       # Tab database lexical
│   └── thesaurus.html     # Tab tesaurus
├── wordlist/
│   └── generator.html     # Tab wordlist generator
├── quran/
│   └── index.html         # Tab index Al-Quran
└── stats/
    └── system.html        # Tab statistik sistem
```

**Fitur Baru:**
- ✅ **Design Modern** - Header gradient, hover effects, better spacing
- ✅ **Responsive Layout** - Better mobile responsiveness
- ✅ **Loading States** - Progress bars dan loading indicators
- ✅ **Interactive Elements** - Enhanced button styling dan animations
- ✅ **Modular Structure** - Setiap komponen dalam file terpisah untuk maintainability
