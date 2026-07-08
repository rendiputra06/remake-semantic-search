# Design Spec: Data Playground Feature

**Date**: 2026-07-07  
**Status**: APPROVED  
**Author**: Antigravity AI Coding Assistant  

---

## 1. Overview & Goal

The **Data Playground** is a new interactive sandbox page designed to visualize the step-by-step business logic transformations in the semantic search pipeline. It helps developers and researchers inspect text preprocessing, query vectorization, cosine similarity computation, threshold filtering, and dynamic evaluation metrics calculation in a dual-panel interface.

---

## 2. User Review Required & Design Decisions

*   **Interactive Flowchart**: The right-hand panel renders an animated vertical flowchart depicting the 7 pipeline steps. Clicking any step dynamically switches the left-hand panel.
*   **Client-Side Computation**: Preprocessing and similarity score data are fetched once from the backend. Thresholding, Ground Truth comparison, and Precision/Recall/F1 calculations are performed on the client-side (JavaScript) to enable real-time UI updates when sliders or relevant verse tags are modified.

---

## 3. Proposed Changes

### [Component: Routing & Controllers]

#### [MODIFY] [public.py](file:///c:/Users/Rendi/coding/project/semantic/app/public.py)
Add the page route for rendering the new playground template:
```python
@public_bp.route('/playground')
def playground():
    """Halaman Data Playground untuk simulasi logika bisnis pencarian semantik."""
    return render_template('playground.html')
```

#### [NEW] [playground.py](file:///c:/Users/Rendi/coding/project/semantic/app/api/routes/playground.py)
Create a new API blueprint for playground sandbox tracing. The API will execute the search pipeline up to similarity score generation and return detailed data lists:
```python
# API to compute step-by-step tracing data for a query
@playground_api_bp.route('/run', methods=['POST'])
def run_playground_simulation():
    # Receives: query_text, model_type, threshold
    # Preprocesses query using backend.preprocessing
    # Vectorizes query and calculates raw cosine similarity scores for top 100 verses
    # Returns all step-by-step state data as JSON
```

---

### [Component: Frontend & Assets]

#### [NEW] [playground.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground.html)
A new HTML template representing the Playground view:
*   **Header**: Standard navbar integration.
*   **Left Column (60%)**: Detailed status/data transformation display container.
*   **Right Column (40%)**: CSS-animated interactive flowchart SVG representing the pipeline steps.

#### [NEW] [main.js](file:///c:/Users/Rendi/coding/project/semantic/static/js/playground/main.js)
Modular JS script that:
*   Initializes inputs and event listeners (slider dragging, tags adding/removing).
*   Performs AJAX request to `/api/playground/run`.
*   Handles active state tracking of the flowchart nodes.
*   Recalculates TP, FP, FN counts and Precision, Recall, and F1 metrics locally.

---

## 4. Verification & Testing

### Manual Verification
1. Open `/playground` in browser.
2. Select FastText model, set threshold to `0.5`, enter query `"surga"`, and input Ground Truth `"2:255, 3:190"`.
3. Press **Simulasikan**.
4. Verify that clicking flowchart steps displays matching intermediate values (e.g. tokenized list, vector dimensions, raw cosine scores table).
5. Drag similarity threshold slider to `0.6` and confirm the Step 5 (Filtered results) and Step 7 (Evaluation metrik) update instantly without server requests.
6. Remove Ground Truth `"3:190"` and verify metrics values adjust immediately.
