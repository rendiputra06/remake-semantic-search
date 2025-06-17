# API Route Improvement Tasks

## Current Status

Beberapa perbaikan telah dimulai dan sebagian besar task utama telah selesai, namun masih ada beberapa item yang perlu ditangani:

- Struktur direktori dasar di `/app/api/` telah dibuat
- Rute-rute telah dipindahkan ke file yang sesuai
- Implementasi validasi schema telah selesai
- Layer service telah diimplementasikan
- Format response API telah distandarisasi
- Blueprint telah diorganisir dengan baik
- Masih ada beberapa masalah template dan struktur data yang perlu diperbaiki

## Pending Tasks

### 1. Route Consolidation ✓

- [x] Move remaining routes from `/backend/api.py` to appropriate files in `/app/api/routes/`:
  - [x] Search routes to `routes/search.py` - Completed 16/06/2025
  - [x] Statistics routes to `routes/statistics.py` - Completed 16/06/2025
  - [x] Thesaurus routes to `routes/thesaurus.py` - Completed 16/06/2025
  - [x] Export routes to `routes/export.py` - Completed 16/06/2025
  - [x] Model routes to `routes/models.py` - Completed 16/06/2025

### 2. Schema Validation ✓

- [x] Complete schema implementations in `/app/api/schemas/`:
  - [x] Add SearchRequestSchema validation - Completed 16/06/2025
  - [x] Add ThesaurusSchema validation - Completed 16/06/2025
  - [x] Add StatisticsSchema validation - Completed 16/06/2025
  - [x] Add ExportRequestSchema validation - Completed 16/06/2025
  - [x] Add error response schemas - Completed 16/06/2025

### 3. Service Layer Implementation ✓

- [x] Create and implement services in `/app/api/services/`:
  - [x] SearchService - Completed 16/06/2025
  - [x] ThesaurusService - Completed 16/06/2025
  - [x] StatisticsService - Completed 16/06/2025
  - [x] ExportService - Completed 16/06/2025
  - [x] QuranIndexService - Completed 16/06/2025

### 4. Response Standardization ✓

- [x] Implement consistent response format across all endpoints:
  ```json
  {
    "success": boolean,
    "data": object | null,
    "message": string | null,
    "error": string | null
  }
  ```
- [x] Add proper HTTP status codes for all responses
- [x] Implement error handling middleware
- [ ] Fix template errors related to data structure
- [ ] Add Jinja2 custom filters (strftime, etc.)

### 5. Blueprint Organization ✓

- [x] Create and register separate blueprints:
  - [x] Search blueprint (`search_bp`) - `/api/search`
  - [x] Statistics blueprint (`stats_bp`) - `/api/statistics`
  - [x] Thesaurus blueprint (`thesaurus_bp`) - `/api/thesaurus`
  - [x] Export blueprint (`export_bp`) - `/api/export`
  - [x] Model management blueprint (`models_bp`) - `/api/models`
  - [x] Quran index blueprint (`quran_index_bp`) - `/api/quran/index`
- [x] Update template context structure
- [x] Fix template rendering issues

### 6. Authentication & Authorization

- [ ] Add proper auth middleware to protected routes
- [ ] Implement role-based access control
- [ ] Add rate limiting for API endpoints
- [ ] Add session management
- [ ] Implement secure password handling

### 7. Cleanup & Maintenance

- [ ] Remove duplicate routes from `backend/api.py`
- [ ] Update frontend API calls to use new routes
- [ ] Add API documentation using OpenAPI/Swagger
- [ ] Add integration tests for new route structure
- [ ] Fix template errors in admin.html and settings.html
- [ ] Update model status structure
- [ ] Add proper error logging
- [ ] Implement proper date formatting in templates

## Implementation Priority

1. Fix template errors and data structure issues
2. Add authentication improvements
3. Complete cleanup tasks
4. Add documentation and testing
5. Update frontend

## Notes

- Perlu memperbaiki struktur data yang dikirim ke template
- Tambahkan filter Jinja2 yang diperlukan
- Perbaiki penanganan error di template
- Format response API telah distandarisasi
- Blueprint telah diorganisir dengan baik
- Tambahkan logging yang lebih baik
- Pertimbangkan untuk menambahkan versioning API
- Update dokumentasi sesuai perubahan
