# Documentation: Evaluation System V4 (Custom CSV Override)

## Overview
Evaluation System Version 4 allows administrators to define static evaluation results for specific queries using a CSV file. This overrides the real-time search engine evaluation, providing a way to present curated benchmarks or corrected metrics.

## Features
1.  **Custom Result Override:**
    - Checks the database for a matching topic (query).
    - If found, returns the pre-defined metrics (Precision, Recall, F1, etc.) from the CSV.
    - If not found, falls back to the standard V3 evaluation logic (Ensemble/Lexical/Semantic).

2.  **Admin Management:**
    - Upload CSV/Excel files to bulk insert/update custom evaluation data.
    - View list of currently stored custom evaluations.
    - Delete individual custom evaluation entries.

## Technical Implementation

### Database Schema
A new table `custom_evaluations` has been added to `backend/db.py`:

```sql
CREATE TABLE custom_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT UNIQUE NOT NULL,
    w2v_threshold REAL,
    ft_threshold REAL,
    gv_threshold REAL,
    precision REAL,
    recall REAL,
    f1_score REAL,
    tp INTEGER,
    fp INTEGER,
    fn INTEGER,
    created_at TEXT NOT NULL
)
```

### API Endpoint
- **URL:** `/api/evaluation_v4/<query_id>/run`
- **Method:** `POST`
- **Logic:**
  1.  Extract `query_text` from request.
  2.  Call `get_custom_evaluation(query_text)`.
  3.  **IF EXISTS:** Return JSON with `method: "custom_override"` and metrics from DB.
  4.  **IF NOT EXISTS:** Execute standard search logic (V3).

### Admin Interface
- **URL:** `/admin/custom_eval`
- **Upload Route:** `/admin/custom_eval/upload`
- **CSV Format:**
  The CSV **MUST** contain the following headers (case-sensitive):
  - `Topic`
  - `W2V_Threshold`
  - `FT_Threshold`
  - `GV_Threshold`
  - `Precision`
  - `Recall`
  - `F1_Score`
  - `TP`
  - `FP`
  - `FN`

## Usage Guide

### How to Add Custom Results
1.  Log in to the Admin Panel.
2.  Navigate to **Custom Evaluation**.
3.  Prepare a CSV file matching the format above (see `docs/test.csv` for example).
4.  Upload the file.
5.  The system will process and store the data. Existing topics will be updated (if Overwrite is checked/default).

### How to Verify
1.  Go to `/evaluasi/v4`.
2.  Enter a query that exists in your uploaded CSV.
3.  The result should appear almost instantly (execution time ~0.05s) and match the CSV metrics exactly.
4.  Enter a random query. The result should take longer and be calculated by the engine.

## File Changes
- **Backend:** `backend/db.py` (Schema & Helpers)
- **API:** `app/api/routes/evaluation_v4.py` (New Logic), `app/api/__init__.py` (Registration)
- **Routes:** `app/admin/routes.py` (Admin Page), `app/public.py` (Public Page)
- **Frontend:** `templates/evaluasi_v4.html`, `templates/admin_custom_eval.html`, `static/js/evaluasi_v4/`
