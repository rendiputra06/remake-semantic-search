# Design Spec: Indexing Phase Lab Page in Data Playground

**Date**: 2026-07-10  
**Status**: APPROVED  
**Author**: Antigravity AI Coding Assistant  

---

## 1. Overview & Goal

The goal is to create a dedicated page, **Laboratorium Fasa Pengindeksan (Indexing Phase Lab)**, specifically for simulating and explaining the offline indexing pipeline of Al-Quran corpus text into embedding vector indices. 

The feature highlights:
1.  A dropdown selector to choose a short surah (Al-Fatihah, Al-Ikhlas, Al-Falaq, An-Nas) and an embedding model (Word2Vec, FastText, GloVe).
2.  A split-pane interface showing the list of verses on the left and a three-tab view on the right:
    *   **Visual Mode**: Graphical pipeline visualizing the step-by-step conversion of text to vectors and database insertion.
    *   **Pseudocode**: The logical algorithm explaining how indexing works.
    *   **Coding**: Actual backend Python code used in this application.
3.  A navigation button inside the main playground page to allow users to switch pages seamlessly.

---

## 2. Proposed Changes

### [Component: Routing & Controllers]

#### [MODIFY] [public.py](file:///c:/Users/Rendi/coding/project/semantic/app/public.py)
Add the page route for rendering the new playground indexing template:
```python
@public_bp.route('/playground/indexing')
def playground_indexing():
    """Halaman Data Playground khusus untuk simulasi fasa pengindeksan."""
    return render_template('playground_indexing.html')
```

#### [MODIFY] [playground.py](file:///c:/Users/Rendi/coding/project/semantic/app/api/routes/playground.py)
Create a new API blueprint route `/indexing/simulate` to process a selected surah's verses and return step-by-step trace metadata:
```python
@playground_api_bp.route('/indexing/simulate', methods=['POST'])
def run_indexing_simulation():
    # Receives: surah_number, model_type
    # Fetches verses via get_verses_by_surah(surah_number)
    # Traces step-by-step preprocessing (lowercase, punctuation, tokenization, stopword removal)
    # Extracts average vector using active embedding model
    # Constructs SQLite database mock payload query
    # Returns structured tracing data list
```

---

## 3. [Component: Frontend & Assets]

#### [MODIFY] [playground.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground.html)
Add a header button on the top-right of the title section linking to `/playground/indexing`:
```html
<a href="/playground/indexing" class="btn btn-outline-primary btn-sm"><i class="fas fa-microscope me-1"></i>Ke Lab Pengindeksan</a>
```

#### [NEW] [playground_indexing.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground_indexing.html)
A new HTML template representing the Indexing Lab view:
*   Header: Navigation back button and page title.
*   Config panel: Dropdowns for Surah and Model, and a "Jalankan Pengindeksan" button.
*   Verse List Panel (left 35%): Displays list of verses for clicked surah.
*   Tab Panel (right 65%): Standard Bootstrap tabs:
    *   `#tab-visual`: Interactive visual flow pipeline from raw document to SQLite storage.
    *   `#tab-pseudocode`: Formatted algorithm pseudocode block.
    *   `#tab-code`: Formatted python implementation snippet.

#### [NEW] [indexing.js](file:///c:/Users/Rendi/coding/project/semantic/static/js/playground/indexing.js)
Modular JS script that:
*   Sends POST request to `/api/playground/indexing/simulate`.
*   Manages selected active verse state and UI tab switching.
*   Renders dynamic Visual Mode node updates.

---

## 4. Verification & Testing

### Manual Verification
1.  Open `/playground` in browser. Verify that the "Ke Lab Pengindeksan" button is visible and redirects to `/playground/indexing`.
2.  On `/playground/indexing`, select Surah "Al-Fatihah" and model "Word2Vec", then click "Jalankan Pengindeksan".
3.  Confirm that the left panel is populated with Al-Fatihah's 7 verses.
4.  Click Verse 1, click "Visual Mode" tab, and verify that the visual workflow maps:
    *   Raw translation text
    *   Filtered tokens
    *   Vector size (200 dimensions) and first few values
    *   Mock insert database statement
5.  Click the "Pseudocode" and "Coding" tabs and verify code structures display correctly.
