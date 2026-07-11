/**
 * JS Module for Vector Explorer (Academic Research Theme)
 * Manages 200-dimensional matrix-style numbers, preprocessing pipelines, word pooling breakdowns,
 * and element-wise product comparisons without color heatmaps.
 */

function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener("DOMContentLoaded", () => {
    // Local State
    const state = {
        modelType: 'word2vec',
        page: 1,
        limit: 20,
        search: '',
        matchWord: '',
        wordVector: null,
        versesData: [],
        currentDetailData: null // Stores response from /details endpoint
    };

    // DOM Elements
    const modelSelect = document.getElementById("model-type");
    const matchWordInput = document.getElementById("match-word");
    const btnMatch = document.getElementById("btn-match");
    const btnClearMatch = document.getElementById("btn-clear-match");
    const searchFilter = document.getElementById("search-filter");
    const wordVectorCard = document.getElementById("word-vector-card");
    const displayMatchedWord = document.getElementById("display-matched-word");
    const wordVectorMag = document.getElementById("word-vector-mag");
    const wordVectorPreviewBox = document.getElementById("word-vector-preview-box");
    const btnDownloadWordJson = document.getElementById("btn-download-word-json");
    const btnShowFullWordVector = document.getElementById("btn-show-full-word-vector");
    
    const loader = document.getElementById("explorer-loader");
    const loaderDetails = document.getElementById("loader-details");
    const explorerContent = document.getElementById("explorer-content");
    const versesTbody = document.getElementById("verses-tbody");
    
    const paginationInfo = document.getElementById("pagination-info");
    const paginationControls = document.getElementById("pagination-controls");

    // Modal Compare Elements
    const modalVerseTitle = document.getElementById("modal-verse-title");
    const modalVerseArabic = document.getElementById("modal-verse-arabic");
    const modalVerseTranslation = document.getElementById("modal-verse-translation");
    const modalMatchWord = document.getElementById("modal-match-word");
    const modalModelType = document.getElementById("modal-model-type");
    const modalSimilarityScore = document.getElementById("modal-similarity-score");
    
    const modalPrepLowercase = document.getElementById("modal-prep-lowercase");
    const modalPrepPunct = document.getElementById("modal-prep-punct");
    const modalPrepTokens = document.getElementById("modal-prep-tokens");
    
    const modalDimLabel = document.getElementById("modal-dim-label");
    const modalMagLabel = document.getElementById("modal-mag-label");
    const modalPoolingTbody = document.getElementById("modal-pooling-tbody");
    
    const modalStepSimilarityCard = document.getElementById("modal-step-similarity-card");
    const modalQueryWordText = document.getElementById("modal-query-word-text");
    const modalDocRefText = document.getElementById("modal-doc-ref-text");
    const modalQueryVecPreview = document.getElementById("modal-query-vec-preview");
    const modalDocVecPreview = document.getElementById("modal-doc-vec-preview");
    const modalDotProductBarCells = document.getElementById("modal-dot-product-bar-cells");
    const modalSimilarityScoreVal = document.getElementById("modal-similarity-score-val");
    const btnDownloadCompareJson = document.getElementById("btn-download-compare-json");

    // Full Vector Viewer Modal Elements
    const vectorModalLabel = document.getElementById("vectorModalLabel");
    const vectorModalSubtitle = document.getElementById("vectorModalSubtitle");
    const modalDimsViewer = document.getElementById("modal-dims-viewer");
    const modalMagViewer = document.getElementById("modal-mag-viewer");
    const modalModelViewer = document.getElementById("modal-model-viewer");
    const vectorFullGrid = document.getElementById("vector-full-grid");

    let compareModalInstance = null;
    let viewerModalInstance = null;

    // Startup
    loadExplorerData();

    // Event Listeners
    modelSelect.addEventListener("change", (e) => {
        state.modelType = e.target.value;
        state.page = 1;
        loadExplorerData();
    });

    btnMatch.addEventListener("click", () => {
        const val = matchWordInput.value.trim();
        if (val) {
            state.matchWord = val;
            state.page = 1;
            loadExplorerData();
        } else {
            Swal.fire("Info", "Masukkan satu kata untuk dicocokkan terlebih dahulu.", "info");
        }
    });

    matchWordInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            btnMatch.click();
        }
    });

    btnClearMatch.addEventListener("click", () => {
        matchWordInput.value = "";
        state.matchWord = "";
        state.wordVector = null;
        wordVectorCard.classList.add("d-none");
        state.page = 1;
        loadExplorerData();
    });

    // Debounce search filter
    let searchTimeout;
    searchFilter.addEventListener("input", (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.search = e.target.value.trim();
            state.page = 1;
            loadExplorerData();
        }, 400);
    });

    btnDownloadWordJson.addEventListener("click", () => {
        if (!state.wordVector || !state.matchWord) return;
        downloadJSON(
            {
                word: state.matchWord,
                model_type: state.modelType,
                dimensions: state.wordVector.length,
                vector: state.wordVector
            },
            `vector_word_${state.matchWord.toLowerCase()}_${state.modelType}.json`
        );
    });

    btnDownloadCompareJson.addEventListener("click", () => {
        if (!state.currentDetailData || !state.wordVector) return;
        const d = state.currentDetailData;
        const wVec = state.wordVector;
        const vVec = d.final_vector;
        const prod = wVec.map((w, i) => w * vVec[i]);
        const sumProd = prod.reduce((a, b) => a + b, 0);

        downloadJSON(
            {
                word: state.matchWord,
                verse_ref: d.verse_id,
                surah_name: d.surah_name,
                model_type: state.modelType,
                cosine_similarity: sumProd,
                word_vector: wVec,
                verse_vector: vVec,
                element_wise_product: prod
            },
            `vector_compare_${state.matchWord.toLowerCase()}_verse_${d.verse_id.replace(':', '_')}.json`
        );
    });

    // Show full word vector click
    btnShowFullWordVector.addEventListener("click", () => {
        if (!state.wordVector || !state.matchWord) return;
        openVectorViewerModal(
            `Kata: "${state.matchWord}"`,
            state.matchWord,
            state.wordVector,
            1.0
        );
    });

    // Functions
    async function loadExplorerData() {
        showLoader(true);
        
        if (state.modelType === 'ensemble' && state.versesData.length === 0) {
            loaderDetails.textContent = "Menginisialisasi model dasar (Word2Vec, FastText, GloVe) dan menyusun matriks ensemble rata-rata. Proses ini memerlukan waktu 10-15 detik pertama.";
        } else {
            loaderDetails.textContent = "Menghubungi API server untuk memproses data vektor.";
        }

        try {
            const url = `/api/vector-explorer/query?model_type=${state.modelType}&page=${state.page}&limit=${state.limit}&search=${encodeURIComponent(state.search)}&match_word=${encodeURIComponent(state.matchWord)}`;
            const response = await fetch(url);
            const resData = await response.json();

            if (resData.success) {
                state.versesData = resData.data;
                
                // Set word vector if returned
                if (resData.word_vector) {
                    state.wordVector = resData.word_vector;
                    displayMatchedWord.textContent = `"${state.matchWord}"`;
                    wordVectorMag.textContent = "1.0000";
                    wordVectorPreviewBox.textContent = `[ ${state.wordVector.slice(0, 10).map(v => v.toFixed(4)).join(", ")}, ... ]`;
                    wordVectorCard.classList.remove("d-none");
                } else {
                    state.wordVector = null;
                    wordVectorCard.classList.add("d-none");
                }

                renderTable(resData.total_verses);
                renderPagination(resData.total_pages, resData.current_page, resData.total_verses);
                showLoader(false);
            } else {
                showLoader(false);
                Swal.fire("Gagal", resData.message || "Gagal memuat data", "error");
            }
        } catch (err) {
            showLoader(false);
            Swal.fire("Error", "Kesalahan koneksi ke server: " + err.message, "error");
        }
    }

    function showLoader(show) {
        if (show) {
            loader.classList.remove("d-none");
            explorerContent.classList.add("d-none");
        } else {
            loader.classList.add("d-none");
            explorerContent.classList.remove("d-none");
        }
    }

    function renderTable(totalVerses) {
        versesTbody.innerHTML = "";
        
        if (state.versesData.length === 0) {
            versesTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Tidak ada data ayat yang cocok dengan filter pencarian.</td></tr>';
            return;
        }

        state.versesData.forEach((row) => {
            const tr = document.createElement("tr");

            // Similarity score info
            let simCell = "";
            let btnAction = "";
            if (state.wordVector && typeof row.similarity !== 'undefined') {
                const simPerc = Math.max(0, Math.min(100, row.similarity * 100));
                let bgBadge = "bg-warning-subtle text-warning-emphasis border-warning-subtle";
                let fillBar = "#f59e0b";
                if (row.similarity >= 0.70) {
                    bgBadge = "bg-success-subtle text-success-emphasis border-success-subtle";
                    fillBar = "#10b981";
                } else if (row.similarity < 0.40) {
                    bgBadge = "bg-danger-subtle text-danger-emphasis border-danger-subtle";
                    fillBar = "#ef4444";
                }

                simCell = `
                    <div class="mt-2" style="max-width: 140px;">
                        <div class="d-flex justify-content-between align-items-center mb-1" style="font-size: 0.7rem;">
                            <span class="fw-bold">Similarity</span>
                            <span class="badge ${bgBadge} border font-monospace" style="font-size: 0.65rem;">${row.similarity.toFixed(4)}</span>
                        </div>
                        <div class="similarity-bar-container">
                            <div class="similarity-bar-fill" style="width: ${simPerc}%; background-color: ${fillBar};"></div>
                        </div>
                    </div>
                `;

                btnAction = `
                    <button type="button" class="btn btn-primary btn-sm btn-compare" data-id="${row.verse_id}" title="Bandingkan Dimensi Vektor">
                        <i class="fas fa-balance-scale"></i> Bandingkan
                    </button>
                `;
            } else {
                btnAction = `
                    <button type="button" class="btn btn-outline-secondary btn-sm btn-compare" data-id="${row.verse_id}" title="Detail Ayat & Vektor">
                        <i class="fas fa-expand-alt"></i> Detail
                    </button>
                `;
            }

            const floatsHtml = row.vector.slice(0, 10).map(v => v.toFixed(4)).join(", ");

            tr.innerHTML = `
                <td><strong class="text-primary font-monospace">${row.verse_id}</strong></td>
                <td>
                    <span class="fw-bold text-dark d-block" style="font-size: 0.8rem;">Surah ${row.surah_name}</span>
                    <small class="text-muted">No. ${row.surah_number} | Ayat ${row.ayat_number}</small>
                </td>
                <td>
                    <p class="arabic-text text-end mb-1 fs-6" style="font-family: 'Scheherazade New', serif; color: #1e293b;">${row.arabic}</p>
                    <p class="text-muted mb-0 small text-truncate-custom" style="max-height: 36px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;" title="${row.translation}">
                        ${row.translation}
                    </p>
                    ${simCell}
                </td>
                <td>
                    <span class="badge bg-secondary bg-opacity-10 text-secondary mb-1" style="font-size:0.6rem;">${row.vector.length} Dimensions (L2 Normed)</span>
                    <div class="bg-dark text-warning p-2 rounded font-monospace" style="font-size: 0.72rem; word-break: break-all; min-height:38px;">
                        [ ${floatsHtml}, ... ]
                    </div>
                </td>
                <td class="text-end">
                    ${btnAction}
                </td>
            `;

            versesTbody.appendChild(tr);
        });

        // Register compare action
        document.querySelectorAll(".btn-compare").forEach(btn => {
            btn.addEventListener("click", () => {
                const vid = btn.dataset.id;
                loadVerseDetailsAndOpenModal(vid);
            });
        });
    }

    async function loadVerseDetailsAndOpenModal(verseId) {
        Swal.fire({
            title: 'Memuat Rincian Ayat',
            html: 'Memproses tokenisasi & ekstraksi vektor kata...',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        try {
            const url = `/api/vector-explorer/details?model_type=${state.modelType}&verse_id=${verseId}&match_word=${encodeURIComponent(state.matchWord)}`;
            const response = await fetch(url);
            const data = await response.json();
            Swal.close();

            if (data.success) {
                state.currentDetailData = data;
                populateAndShowModal(data);
            } else {
                Swal.fire("Gagal", data.message || "Gagal memuat rincian", "error");
            }
        } catch (err) {
            Swal.close();
            Swal.fire("Error", "Kesalahan memuat rincian: " + err.message, "error");
        }
    }

    function populateAndShowModal(data) {
        // Set basic details
        modalVerseTitle.textContent = `Surah ${data.surah_name} [${data.verse_id}]`;
        modalVerseArabic.textContent = data.arabic;
        modalVerseTranslation.textContent = data.translation;
        modalMatchWord.textContent = state.matchWord ? `"${state.matchWord}"` : "-";
        modalModelType.textContent = state.modelType;
        
        // Calculate similarity on client side
        let simScore = 0.0;
        if (state.wordVector && data.final_vector) {
            simScore = state.wordVector.reduce((sum, w, i) => sum + (w * data.final_vector[i]), 0);
            modalSimilarityScore.textContent = simScore.toFixed(4);
            modalSimilarityScoreVal.textContent = simScore.toFixed(6);
            modalSimilarityScore.className = "mb-0 fw-bold text-primary";
        } else {
            modalSimilarityScore.textContent = "Tidak ada";
            modalSimilarityScoreVal.textContent = "0.000000";
            modalSimilarityScore.className = "mb-0 fw-bold text-muted";
        }

        // 1. Render Preprocessing Steps
        modalPrepLowercase.textContent = data.preprocessing.lowercase;
        modalPrepPunct.textContent = data.preprocessing.no_punctuation;
        modalPrepTokens.innerHTML = "";
        
        if (data.preprocessing.filtered_tokens.length > 0) {
            data.preprocessing.filtered_tokens.forEach(t => {
                const b = document.createElement("span");
                b.className = "badge bg-success text-white me-1 mb-1 font-monospace p-1";
                b.textContent = t;
                modalPrepTokens.appendChild(b);
            });
        } else {
            modalPrepTokens.innerHTML = '<span class="text-danger italic">Semua token terfilter sebagai stopword.</span>';
        }

        // 2. Render Embedding Pooling Table
        modalPoolingTbody.innerHTML = "";
        modalDimLabel.textContent = `${data.final_vector.length}D`;
        modalMagLabel.textContent = data.final_magnitude.toFixed(6);

        // Populate table rows for each word
        data.token_details.forEach((tok, idx) => {
            const tr = document.createElement("tr");
            
            let vecPreview = "";
            let btnAction = "";

            if (!tok.is_oov && tok.vector) {
                vecPreview = `[ ${tok.vector.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]`;
                btnAction = `
                    <button class="btn btn-outline-secondary py-0 btn-sm btn-show-word-details-vector" 
                            data-word="${escapeHtml(tok.token)}" 
                            data-vec-idx="${idx}"
                            style="font-size:0.65rem; padding: 2px 6px;">
                        <i class="fas fa-expand-alt me-1"></i>200D
                    </button>
                `;
            } else {
                vecPreview = `<span class="text-danger italic">[ OOV - Tidak Terdaftar ]</span>`;
                btnAction = `<span class="text-muted small">-</span>`;
            }

            tr.innerHTML = `
                <td>Vektor kata: <code>"${escapeHtml(tok.token)}"</code></td>
                <td class="font-monospace text-muted">${vecPreview}</td>
                <td class="text-center">${btnAction}</td>
            `;
            modalPoolingTbody.appendChild(tr);
        });

        // Add Mean Pooling row
        const meanTr = document.createElement("tr");
        meanTr.className = "table-info";
        meanTr.style.cssText = "--bs-table-bg: rgba(13, 202, 240, 0.08);";
        meanTr.innerHTML = `
            <td><strong>Rata-rata (Mean Pooling)</strong></td>
            <td class="font-monospace text-dark fw-semibold">[ ${data.mean_vector.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]</td>
            <td class="text-center">
                <button class="btn btn-outline-info py-0 btn-sm btn-show-mean-vector" style="font-size:0.65rem; padding:2px 6px;">
                    <i class="fas fa-expand-alt me-1"></i>200D
                </button>
            </td>
        `;
        modalPoolingTbody.appendChild(meanTr);

        // Add final normalized row
        const finalTr = document.createElement("tr");
        finalTr.className = "table-success";
        finalTr.style.cssText = "--bs-table-bg: rgba(25, 135, 84, 0.08);";
        finalTr.innerHTML = `
            <td><strong>Hasil Akhir (L2 Normalized)</strong></td>
            <td class="font-monospace text-success fw-bold">[ ${data.final_vector.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]</td>
            <td class="text-center">
                <button class="btn btn-outline-success py-0 btn-sm btn-show-final-vector" style="font-size:0.65rem; padding:2px 6px;">
                    <i class="fas fa-expand-alt me-1"></i>200D
                </button>
            </td>
        `;
        modalPoolingTbody.appendChild(finalTr);

        // 3. Render Cosine Retrieval Test Stage if matching word is present
        if (state.wordVector && data.word_vector) {
            modalStepSimilarityCard.classList.remove("d-none");
            modalQueryWordText.textContent = `"${state.matchWord}"`;
            modalDocRefText.textContent = data.verse_id;
            
            modalQueryVecPreview.textContent = `[ ${state.wordVector.slice(0, 10).map(v => v.toFixed(4)).join(', ')}, ... ]`;
            modalDocVecPreview.textContent = `[ ${data.final_vector.slice(0, 10).map(v => v.toFixed(4)).join(', ')}, ... ]`;

            // Draw Dot Product Bar Chart per dimension (first 10 dimensions)
            modalDotProductBarCells.innerHTML = "";
            
            const first10Products = state.wordVector.slice(0, 10).map((w, i) => w * data.final_vector[i]);
            
            first10Products.forEach((prod, i) => {
                const cellWrapper = document.createElement("div");
                cellWrapper.className = "d-flex flex-column align-items-center me-2 position-relative";
                cellWrapper.style.width = "40px";
                
                const bar = document.createElement("span");
                const h = Math.max(4, Math.round(Math.abs(prod) * 600)); // scaling factor for display
                const col = prod >= 0 ? '#10b981' : '#ef4444'; // emerald green or red
                
                bar.style.display = "inline-block";
                bar.style.width = "12px";
                bar.style.height = `${h}px`;
                bar.style.backgroundColor = col;
                bar.style.borderRadius = "2px";
                bar.title = `d${i+1}: ${prod.toFixed(6)}`;
                
                const label = document.createElement("span");
                label.className = "text-muted font-monospace";
                label.style.fontSize = "0.55rem";
                label.textContent = `d${i+1}`;
                
                cellWrapper.appendChild(bar);
                cellWrapper.appendChild(label);
                modalDotProductBarCells.appendChild(cellWrapper);
            });
        } else {
            modalStepSimilarityCard.classList.add("d-none");
        }

        // Register Detail Vector listeners in Compare Modal
        modalPoolingTbody.querySelectorAll(".btn-show-word-details-vector").forEach(btn => {
            btn.addEventListener("click", () => {
                const tokWord = btn.dataset.word;
                const idx = parseInt(btn.dataset.vecIdx);
                const vector = data.token_details[idx].vector;
                openVectorViewerModal(`Kata: "${tokWord}"`, tokWord, vector, 1.0);
            });
        });

        modalPoolingTbody.querySelector(".btn-show-mean-vector").addEventListener("click", () => {
            openVectorViewerModal("Rata-rata Mean Pooling", data.verse_id, data.mean_vector, 1.0);
        });

        modalPoolingTbody.querySelector(".btn-show-final-vector").addEventListener("click", () => {
            openVectorViewerModal("Hasil Akhir L2 Normalized", data.verse_id, data.final_vector, 1.0);
        });

        const showWordDetailsBtn = modalStepSimilarityCard.querySelector(".btn-show-word-details-vector");
        if (showWordDetailsBtn) {
            showWordDetailsBtn.onclick = () => {
                openVectorViewerModal(`Kata Kueri: "${state.matchWord}"`, state.matchWord, state.wordVector, 1.0);
            };
        }

        const showVerseDetailsBtn = modalStepSimilarityCard.querySelector(".btn-show-verse-details-vector");
        if (showVerseDetailsBtn) {
            showVerseDetailsBtn.onclick = () => {
                openVectorViewerModal(`Akhir L2: Ayat ${data.verse_id}`, data.verse_id, data.final_vector, 1.0);
            };
        }

        // Open modal
        const modalEl = document.getElementById("compareModal");
        compareModalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
        compareModalInstance.show();
    }

    function openVectorViewerModal(title, subtitle, vector, magnitude) {
        vectorModalLabel.innerHTML = `<i class="fas fa-vector-square me-2"></i>Vektor Lengkap: ${title}`;
        vectorModalSubtitle.textContent = `Identifikasi: ${subtitle} \u2014 ${state.modelType.toUpperCase()}`;
        modalDimsViewer.textContent = `${vector.length}D`;
        modalMagViewer.textContent = magnitude.toFixed(6);
        modalModelViewer.textContent = state.modelType;

        // Build grid cells
        vectorFullGrid.innerHTML = "";
        vector.forEach((val, i) => {
            const cell = document.createElement("div");
            cell.className = "vector-cell";
            cell.title = `Dimensi ${i + 1}: ${val}`;
            cell.innerHTML = `<span class="dim-label">d${i+1}</span><span class="dim-val">${val.toFixed(5)}</span>`;
            vectorFullGrid.appendChild(cell);
        });

        // Show viewer modal
        const modalEl = document.getElementById("vectorModal");
        viewerModalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
        viewerModalInstance.show();
    }

    function renderPagination(totalPages, currentPage, totalVerses) {
        paginationControls.innerHTML = "";
        
        const start = ((currentPage - 1) * state.limit) + 1;
        const end = Math.min(currentPage * state.limit, totalVerses);
        paginationInfo.textContent = totalVerses > 0 
            ? `Menampilkan ${start}-${end} dari ${totalVerses} ayat` 
            : `Menampilkan 0-0 dari 0 ayat`;

        if (totalPages <= 1) return;

        const maxButtons = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = startPage + maxButtons - 1;
        
        if (endPage > totalPages) {
            endPage = totalPages;
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        // Previous button
        const prevLi = document.createElement("li");
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<button class="page-link" type="button">&laquo;</button>`;
        if (currentPage > 1) {
            prevLi.addEventListener("click", () => {
                state.page = currentPage - 1;
                loadExplorerData();
            });
        }
        paginationControls.appendChild(prevLi);

        // Page number buttons
        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement("li");
            li.className = `page-item ${i === currentPage ? 'active' : ''}`;
            li.innerHTML = `<button class="page-link" type="button">${i}</button>`;
            li.addEventListener("click", () => {
                state.page = i;
                loadExplorerData();
            });
            paginationControls.appendChild(li);
        }

        // Next button
        const nextLi = document.createElement("li");
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<button class="page-link" type="button">&raquo;</button>`;
        if (currentPage < totalPages) {
            nextLi.addEventListener("click", () => {
                state.page = currentPage + 1;
                loadExplorerData();
            });
        }
        paginationControls.appendChild(nextLi);
    }

    function downloadJSON(data, filename) {
        const payload = JSON.stringify(data, null, 2);
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});
