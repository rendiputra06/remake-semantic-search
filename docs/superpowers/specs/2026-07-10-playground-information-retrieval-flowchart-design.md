# Design Spec: Information Retrieval Pipeline Flowchart for Data Playground

**Date**: 2026-07-10  
**Status**: APPROVED  
**Author**: Antigravity AI Coding Assistant  

---

## 1. Overview & Goal

The user wants to align the right-hand flowchart panel in the standard single model playground page with the architectural diagram of an Information Retrieval (IR) application (**Figure 3.1**). 

The goal is to replace the simple vertical list of 7 steps with an interactive, responsive SVG block diagram layout representing the two distinct phases of the system:
1.  **Indexing Phase** (corresponds to offline corpus indexing: Raw Document -> Pre-processing -> Single-View Semantic -> Indexed Document).
2.  **Searching Phase** (corresponds to online search execution: Query -> Similarity Calculation -> Results: Quran Verse -> Performance Assessment).

---

## 2. Interactive Flowchart Layout (SVG Specs)

The right-hand panel in [playground.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground.html) will render an SVG block diagram with a viewBox of `0 0 320 500`.

### Coordinate Blueprint
*   **Indexing Phase Bounding Box**: `x=10`, `y=10`, `width=300`, `height=200`, dashed border, label: "Indexing Phase".
    *   **Node 1 (Raw Document)**: Center X: `160`, Y: `25` (rendered as database cylinder cylinder shape).
    *   **Node 2 (Pre-processing)**: Center X: `160`, Y: `75` (rounded rect).
    *   **Node 3 (Single-View Semantic)**: Center X: `160`, Y: `125` (rounded rect).
    *   **Node 4 (Indexed Document)**: Center X: `160`, Y: `175` (rounded rect).
*   **Searching Phase Bounding Box**: `x=10`, `y=230`, `width=300`, `height=250`, dashed border, label: "Searching Phase".
    *   **Node 5 (Query)**: Center X: `75`, Y: `270` (rounded rect).
    *   **Node 6 (Similarity Calculation)**: Center X: `225`, Y: `270` (rounded rect).
    *   **Node 7 (Results: Quran Verse)**: Center X: `225`, Y: `340` (rounded rect).
    *   **Node 8 (Performance Assessment)**: Center X: `225`, Y: `420` (rounded rect with multiple labels inside: Precision, Recall, F1-Score).

---

## 3. Proposed Changes

### [Component: Frontend & Scripts]

#### [MODIFY] [playground.html](file:///c:/Users/Rendi/coding/project/semantic/templates/playground.html)
*   Replace the vertical list inside the right-hand card with an SVG diagram matching the coordinate blueprint.
*   Add inline CSS styling for SVG components supporting class `.flow-node` and `.flow-arrow` state changes.
*   Maintain the active green pulse circle on the selected node.

#### [MODIFY] [main.js](file:///c:/Users/Rendi/coding/project/semantic/static/js/playground/main.js)
*   Expand step states from 7 to 8.
*   Adjust `changeStep(stepIndex)` range check and logic.
*   Update `renderActiveStep()` mappings:
    *   **Step 1 (Raw Document)**: Renders Quran corpus database statistics (surahs, ayats, database format, languages).
    *   **Step 2 (Pre-processing)**: Renders Corpus preprocessing configurations.
    *   **Step 3 (Single-View Semantic)**: Renders metadata about the embedding model (vector dimensions, skip-gram/cbow details, training vocab size).
    *   **Step 4 (Indexed Document)**: Renders index details (verse_vectors table size, vector index status).
    *   **Step 5 (Query)**: Renders query preprocessing details (lowercase, punctuation removal, token weight sandbox, synonyms search). *(Old Step 2)*.
    *   **Step 6 (Similarity Calculation)**: Renders vector space extraction (norm, dimensions), 2D SVD scatter plot (Chart.js), and top 10 raw similarity score table. *(Old Step 3 + 4)*.
    *   **Step 7 (Results: Quran Verse)**: Renders dynamic similarity threshold filter results table (passed vs failed) and Ground Truth TP, FP, FN categorization. *(Old Step 5 + 6)*.
    *   **Step 8 (Performance Assessment)**: Renders Precision, Recall, and F1-score with step-by-step formula evaluation. *(Old Step 7)*.

---

## 4. Verification & Testing

### Manual Verification
1.  Open `/playground` in a browser.
2.  Inspect the SVG flowchart in the right panel and check if it resembles Figure 3.1 structure.
3.  Click through steps 1-4 (Indexing Phase) and verify that static/config information about database, corpus preprocessing, and selected models loads correctly.
4.  Run a simulation with query "iman". Verify that Steps 5-8 (Searching Phase) unlock and show appropriate query preprocessing, Chart.js scatter plots, threshold filtering, and dynamic precision/recall updates when changing thresholds.
