/**
 * Main JS Module for Data Playground (Academic Research Theme)
 * Manages query list selection via modal, interactive state, UI stepper, and local evaluations.
 */

document.addEventListener("DOMContentLoaded", () => {
    // State management
    let state = {
        activeStep: 1,
        activeQueryId: null,
        activeQueryText: "",
        simulationData: null,
        threshold: 0.50,
        groundTruth: [],
        tokenWeights: {}
    };

    // Chart instance
    let vectorSpaceChartInstance = null;

    // DOM Elements
    const queryList = document.getElementById("query-list");
    const queryCount = document.getElementById("query-count");
    const querySearchInput = document.getElementById("query-search");
    const activeQueryDisplay = document.getElementById("active-query-display");
    const form = document.getElementById("playground-form");
    const modelSelect = document.getElementById("model-type");
    const thresholdInput = document.getElementById("similarity-threshold");
    const thresholdVal = document.getElementById("threshold-val");
    const groundTruthInput = document.getElementById("ground-truth");
    const simulateBtn = document.getElementById("btn-simulate");
    const resetBtn = document.getElementById("btn-reset");
    const detailPanel = document.getElementById("detail-panel");
    const flowNodes = document.querySelectorAll(".flow-node");
    const flowArrows = document.querySelectorAll(".flow-arrow");

    // Load queries on startup
    loadQueries();

    // Model select change handler to keep state consistent
    modelSelect.addEventListener("change", () => {
        if (state.simulationData) {
            // Reset simulation data and return to step 1 to prevent inconsistent displays
            state.simulationData = null;
            state.activeStep = 1;
            
            // Highlight flow node paths
            highlightFlowchart(false);
            flowNodes.forEach(node => node.classList.remove("active"));
            flowNodes[0].classList.add("active");
            flowArrows.forEach(arrow => {
                arrow.classList.remove("active");
                arrow.setAttribute("marker-end", "url(#arrow-inactive)");
            });
            
            renderActiveStep();
            
            Swal.fire({
                icon: 'warning',
                title: 'Model Berubah',
                text: 'Model embedding telah diubah. Silakan jalankan simulasi kembali.',
                timer: 2000,
                showConfirmButton: false
            });
        } else if (state.activeStep > 4) {
            state.activeStep = 1;
            renderActiveStep();
        } else {
            renderActiveStep();
        }
    });

    // Fetch queries from DB
    async function loadQueries() {
        try {
            const response = await fetch("/api/query");
            const resData = await response.json();
            
            if (resData.success && resData.data) {
                renderQueries(resData.data);
            } else {
                queryList.innerHTML = `<div class="p-3 text-center text-danger small">Gagal memuat query.</div>`;
            }
        } catch (err) {
            queryList.innerHTML = `<div class="p-3 text-center text-danger small">Error: ${err.message}</div>`;
        }
    }

    // Render queries to modal list
    function renderQueries(queries) {
        if (queries.length === 0) {
            queryList.innerHTML = `<div class="p-3 text-center text-muted small">Tidak ada query tersedia.</div>`;
            queryCount.textContent = "0";
            return;
        }

        queryCount.textContent = queries.length;
        queryList.innerHTML = queries.map(q => `
            <button type="button" class="list-group-item list-group-item-action query-item" data-id="${q.id}" data-text="${q.text}">
                <div class="d-flex w-100 justify-content-between align-items-center">
                    <span class="text-truncate query-text-content" style="font-size: 0.88rem; max-width: 90%; color: #334155;">
                        <i class="fas fa-quote-left text-muted me-2" style="font-size: 0.75rem;"></i>${escapeHtml(q.text)}
                    </span>
                    <i class="fas fa-chevron-right text-muted small"></i>
                </div>
            </button>
        `).join("");

        // Add click listener
        document.querySelectorAll(".query-item").forEach(item => {
            item.addEventListener("click", async () => {
                const id = parseInt(item.dataset.id);
                const text = item.dataset.text;
                await selectQuery(id, text, item);
            });
        });
    }

    // Handle query selection from modal
    async function selectQuery(id, text, element) {
        document.querySelectorAll(".query-item").forEach(item => item.classList.remove("active"));
        element.classList.add("active");

        state.activeQueryId = id;
        state.activeQueryText = text;
        activeQueryDisplay.value = text;
        state.tokenWeights = {}; // Reset custom weights
        
        // Fetch Ground Truth
        try {
            const response = await fetch(`/api/query/${id}/relevant_verses`);
            const resData = await response.json();
            
            if (resData.success && resData.data) {
                state.groundTruth = resData.data.map(v => v.verse_ref);
                groundTruthInput.value = state.groundTruth.join(", ");
            } else {
                state.groundTruth = [];
                groundTruthInput.value = "";
            }
        } catch (err) {
            state.groundTruth = [];
            groundTruthInput.value = "";
        }

        // Enable simulate button
        simulateBtn.disabled = false;

        // Reset simulation status if changing query
        state.simulationData = null;
        changeStep(1);

        // Hide Bootstrap modal programmatically
        const modalEl = document.getElementById('queryModal');
        const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    // Search query filter in modal
    querySearchInput.addEventListener("input", (e) => {
        const keyword = e.target.value.toLowerCase().trim();
        document.querySelectorAll(".query-item").forEach(item => {
            const textContent = item.dataset.text.toLowerCase();
            if (textContent.includes(keyword)) {
                item.style.display = "";
            } else {
                item.style.display = "none";
            }
        });
    });

    // Initialize Event Listeners for Sandbox Controllers
    thresholdInput.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        state.threshold = val;
        thresholdVal.textContent = val.toFixed(2);
        
        if (state.simulationData) {
            renderActiveStep();
        }
    });

    groundTruthInput.addEventListener("input", (e) => {
        state.groundTruth = parseGroundTruth(e.target.value);
        
        if (state.simulationData) {
            renderActiveStep();
        }
    });

    flowNodes.forEach(node => {
        node.addEventListener("click", () => {
            const step = parseInt(node.dataset.step);
            changeStep(step);
        });
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await runSimulation();
    });

    // Reset button handler
    resetBtn.addEventListener("click", () => {
        state.activeStep = 1;
        state.activeQueryId = null;
        state.activeQueryText = "";
        state.simulationData = null;
        state.threshold = 0.50;
        state.groundTruth = [];
        state.tokenWeights = {};

        // Clear UI Inputs
        activeQueryDisplay.value = "";
        groundTruthInput.value = "";
        thresholdInput.value = 0.50;
        thresholdVal.textContent = "0.50";
        querySearchInput.value = "";

        // Reset flowchart step active status
        highlightFlowchart(false);
        flowNodes.forEach(node => node.classList.remove("active"));
        flowNodes[0].classList.add("active"); // Set to first step
        flowArrows.forEach(arrow => {
            arrow.classList.remove("active");
            arrow.setAttribute("marker-end", "url(#arrow-inactive)");
        });

        // Disable simulation
        simulateBtn.disabled = true;

        // Reset detail panel
        renderActiveStep();

        // Destroy Chart
        if (vectorSpaceChartInstance) {
            vectorSpaceChartInstance.destroy();
            vectorSpaceChartInstance = null;
        }

        Swal.fire({
            icon: 'info',
            title: 'Playground Direset',
            text: 'Seluruh input parameter dan data simulasi telah dibersihkan.',
            timer: 1500,
            showConfirmButton: false
        });
    });

    // Run search simulation
    async function runSimulation() {
        if (!state.activeQueryText) return;
        const model = modelSelect.value;
        
        simulateBtn.disabled = true;
        simulateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Memproses...';
        
        try {
            const response = await fetch("/api/playground/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query_text: state.activeQueryText,
                    model_type: model,
                    token_weights: state.tokenWeights
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                state.simulationData = data;
                
                // Highlight flow node paths
                highlightFlowchart(true);
                
                // Advance to Step 5 (Query)
                changeStep(5);
                
                Swal.fire({
                    icon: 'success',
                    title: 'Simulasi Selesai',
                    text: 'Jelajahi alur Searching Phase di kanan!',
                    timer: 1800,
                    showConfirmButton: false
                });
            } else {
                Swal.fire("Gagal", data.message || "Terjadi kesalahan", "error");
            }
        } catch (err) {
            Swal.fire("Error", "Gagal menghubungi server: " + err.message, "error");
        } finally {
            simulateBtn.disabled = false;
            simulateBtn.innerHTML = '<i class="fas fa-play me-1"></i>Simulasikan';
        }
    }

    // Step switching logic with safety guard
    function changeStep(stepIndex) {
        if (stepIndex > 4 && !state.simulationData) {
            Swal.fire({
                icon: "info",
                title: "Belum Ada Simulasi",
                text: "Silakan pilih kueri dan tekan tombol 'Simulasikan' terlebih dahulu sebelum melihat langkah fasa pencarian ini.",
                timer: 2200,
                showConfirmButton: false
            });
            return;
        }
        
        state.activeStep = stepIndex;
        
        // Update nodes UI classes
        flowNodes.forEach(node => {
            const nodeStep = parseInt(node.dataset.step);
            if (nodeStep === stepIndex) {
                node.classList.add("active");
            } else {
                node.classList.remove("active");
            }
        });

        // Update arrows UI classes
        flowArrows.forEach(arrow => {
            const arrowIndex = parseInt(arrow.dataset.arrow);
            if (arrowIndex < stepIndex) {
                arrow.classList.add("active");
                arrow.setAttribute("marker-end", "url(#arrow-active)");
            } else {
                arrow.classList.remove("active");
                arrow.setAttribute("marker-end", "url(#arrow-inactive)");
            }
        });

        renderActiveStep();
    }

    // Highlight active flow indicators
    function highlightFlowchart(active) {
        flowNodes.forEach(node => {
            const step = parseInt(node.dataset.step);
            if (active && step <= state.activeStep) {
                node.classList.add("active");
            } else if (!active && step > 1) {
                node.classList.remove("active");
            }
        });
    }

    // Parser for Ground Truth strings
    function parseGroundTruth(inputVal) {
        if (!inputVal) return [];
        return inputVal.split(",")
            .map(v => v.replace(/\s+/g, ''))
            .filter(v => v !== "" && /^\d+:\d+$/.test(v));
    }

    // HTML sanitizer
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.innerText = text;
        return div.innerHTML;
    }

    // Formatter for Ground Truth badge wrapper to prevent long lines overflow
    function formatGroundTruthBadges(verses, borderClass = "secondary") {
        if (!verses || verses.length === 0) {
            return `<span class="text-muted">Tidak ada</span>`;
        }
        const badgesHtml = verses.map(v => `
            <span class="badge bg-${borderClass}-subtle text-${borderClass}-emphasis border border-${borderClass}-subtle me-1 mb-1 font-monospace" style="font-size: 0.72rem;">
                ${v}
            </span>
        `).join("");
        return `<div class="d-flex flex-wrap overflow-auto border border-secondary-subtle rounded bg-light p-2" style="max-height: 80px;">${badgesHtml}</div>`;
    }

    // Bind listeners for token badge synonym inspection and custom weights inputs
    function registerTokenListeners() {
        document.querySelectorAll(".token-weight-input").forEach(input => {
            input.addEventListener("change", (e) => {
                const token = e.target.dataset.token;
                const val = parseFloat(e.target.value) || 1.0;
                state.tokenWeights[token] = val;
            });
        });

        document.querySelectorAll(".token-badge-click").forEach(badge => {
            badge.addEventListener("click", async () => {
                const token = badge.dataset.token;
                const model = modelSelect.value;

                Swal.fire({
                    title: 'Memuat Sinonim...',
                    html: `Mencari kata terdekat untuk <strong>"${token}"</strong>...`,
                    allowOutsideClick: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });

                try {
                    const response = await fetch(`/api/playground/neighbors?word=${token}&model_type=${model}`);
                    const resData = await response.json();

                    if (resData.success && resData.neighbors && resData.neighbors.length > 0) {
                        const listHtml = resData.neighbors.map(n => `
                            <li class="list-group-item d-flex justify-content-between align-items-center py-1">
                                <span class="font-monospace">${n.word}</span>
                                <span class="badge bg-primary-subtle text-primary-emphasis">${n.similarity.toFixed(4)}</span>
                            </li>
                        `).join("");

                        Swal.fire({
                            title: `<i class="fas fa-search me-2 text-primary"></i>Sinonim Kata: "${token}"`,
                            html: `
                                <p class="small text-muted text-start mb-2">10 kata terdekat berdasarkan kedekatan ruang vektor model ${model.toUpperCase()}:</p>
                                <ul class="list-group text-start" style="font-size: 0.88rem;">${listHtml}</ul>
                            `,
                            icon: 'info',
                            confirmButtonText: 'Tutup'
                        });
                    } else {
                        Swal.fire("Info", resData.message || `Kata "${token}" tidak terdaftar dalam model vokabulari.`, "info");
                    }
                } catch (err) {
                    Swal.fire("Error", "Gagal mengambil data sinonim: " + err.message, "error");
                }
            });
        });
    }

    function registerVectorViewListener(values) {
        const btn = document.getElementById("btn-show-full-vector");
        if (btn) {
            btn.addEventListener("click", () => {
                const formattedValues = values.map((v, i) => `
                    <div class="vector-cell" title="Dimensi ${i+1}: ${v}">
                        <span class="dim-label">d${i+1}</span>
                        <span class="dim-val">${v.toFixed(5)}</span>
                    </div>
                `).join("");

                Swal.fire({
                    title: '<i class="fas fa-vector-square me-2 text-primary"></i>Representasi Vektor Kueri',
                    html: `
                        <p class="small text-muted text-start mb-2">Nilai numerik untuk seluruh <strong>${values.length} dimensi</strong> kueri (nilai dinormalisasi L2):</p>
                        <div class="vector-grid bg-dark p-2 rounded text-start">
                            ${formattedValues}
                        </div>
                    `,
                    width: '650px',
                    showDenyButton: true,
                    showCancelButton: false,
                    confirmButtonText: 'Tutup',
                    denyButtonText: '<i class="fas fa-download me-1"></i> Download JSON',
                    denyButtonColor: '#10b981'
                }).then((result) => {
                    if (result.isDenied) {
                        downloadQueryVectorJSON(values);
                    }
                });
            });
        }
    }

    function downloadQueryVectorJSON(values) {
        const payload = JSON.stringify({
            query: state.activeQueryText,
            model_type: modelSelect.value,
            dimensions: values.length,
            vector: values
        }, null, 2);
        
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const safeQuery = state.activeQueryText.toLowerCase().replace(/[^\w\-]/g, '_');
        a.download = `vector_query_${safeQuery}_${modelSelect.value}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function registerVerseVectorListeners(results) {
        document.querySelectorAll(".btn-show-verse-vector").forEach(btn => {
            btn.addEventListener("click", () => {
                const index = parseInt(btn.dataset.index);
                const isFilteredTable = btn.dataset.table === "filtered";
                
                let verse;
                if (isFilteredTable) {
                    const filtered = results.filter(r => r.similarity >= state.threshold);
                    verse = filtered[index];
                } else {
                    verse = results[index];
                }
                
                if (verse && verse.vector_values) {
                    showVerseVectorModal(verse);
                } else {
                    Swal.fire("Info", "Data vektor tidak tersedia untuk ayat ini.", "info");
                }
            });
        });
    }

    function showVerseVectorModal(verse) {
        const values = verse.vector_values;
        const formattedValues = values.map((v, i) => `
            <div class="vector-cell" title="Dimensi ${i+1}: ${v}">
                <span class="dim-label">d${i+1}</span>
                <span class="dim-val">${v.toFixed(5)}</span>
            </div>
        `).join("");

        Swal.fire({
            title: `<i class="fas fa-vector-square me-2 text-success"></i>Vektor Ayat ${verse.surah_number}:${verse.ayat_number}`,
            html: `
                <p class="small text-muted text-start mb-2">Nilai numerik untuk seluruh <strong>${values.length} dimensi</strong> ayat (${verse.surah_name}):</p>
                <div class="vector-grid bg-dark p-2 rounded text-start">
                    ${formattedValues}
                </div>
            `,
            width: '650px',
            showDenyButton: true,
            showCancelButton: false,
            confirmButtonText: 'Tutup',
            denyButtonText: '<i class="fas fa-download me-1"></i> Download JSON',
            denyButtonColor: '#10b981'
        }).then((result) => {
            if (result.isDenied) {
                downloadVerseVectorJSON(verse);
            }
        });
    }

    function downloadVerseVectorJSON(verse) {
        const payload = JSON.stringify({
            verse_ref: `${verse.surah_number}:${verse.ayat_number}`,
            surah_name: verse.surah_name,
            model_type: modelSelect.value,
            dimensions: verse.vector_values.length,
            vector: verse.vector_values
        }, null, 2);
        
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `vector_verse_${verse.surah_number}_${verse.ayat_number}_${modelSelect.value}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Chart.js Scatter Plot rendering
    function drawVectorChart() {
        const canvas = document.getElementById("vectorSpaceChart");
        if (!canvas || !state.simulationData || !state.simulationData.pca || state.simulationData.pca.length === 0) return;

        const pca = state.simulationData.pca;
        const queryPoint = pca.find(p => p.type === 'query');
        const versePoints = pca.filter(p => p.type === 'verse');

        const datasets = [];

        if (queryPoint) {
            datasets.push({
                label: 'Kueri: ' + state.activeQueryText,
                data: [{ x: queryPoint.x, y: queryPoint.y }],
                backgroundColor: '#3b82f6',
                borderColor: '#1d4ed8',
                borderWidth: 2,
                pointRadius: 9,
                pointHoverRadius: 11
            });
        }

        if (versePoints.length > 0) {
            datasets.push({
                label: 'Top 10 Hasil Ayat Terdekat',
                data: versePoints.map(p => ({ x: p.x, y: p.y })),
                backgroundColor: '#10b981',
                borderColor: '#047857',
                borderWidth: 1,
                pointRadius: 6,
                pointHoverRadius: 8
            });
        }

        if (vectorSpaceChartInstance) {
            vectorSpaceChartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        vectorSpaceChartInstance = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#334155',
                            font: { size: 9 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    return 'Kueri Aktif';
                                }
                                const pt = versePoints[context.dataIndex];
                                return pt ? 'Ayat ' + pt.label : 'Ayat';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Komponen Utama 1 (PC1)', color: '#64748b', font: { size: 9 } },
                        grid: { color: '#f1f5f9' },
                        ticks: { color: '#64748b', font: { size: 8 } }
                    },
                    y: {
                        title: { display: true, text: 'Komponen Utama 2 (PC2)', color: '#64748b', font: { size: 9 } },
                        grid: { color: '#f1f5f9' },
                        ticks: { color: '#64748b', font: { size: 8 } }
                    }
                }
            }
        });
    }

    // Stepper Renderer Router
    function renderActiveStep() {
        if (!state.simulationData && state.activeStep > 4) {
            state.activeStep = 1;
        }

        const data = state.simulationData;
        const step = state.activeStep;
        
        let html = "";
        
        switch(step) {
            case 1:
                html = renderStep1RawDoc();
                break;
            case 2:
                html = renderStep2PreprocessingCorpus();
                break;
            case 3:
                html = renderStep3SemanticModel();
                break;
            case 4:
                html = renderStep4IndexedDoc();
                break;
            case 5:
                html = renderStep5Query(data.preprocessing);
                break;
            case 6:
                html = renderStep6Similarity(data.vector, data.results);
                break;
            case 7:
                html = renderStep7Results(data.results);
                break;
            case 8:
                html = renderStep8Performance(data.results);
                break;
            default:
                html = "<h5>Langkah tidak dikenali</h5>";
        }
        
        detailPanel.innerHTML = html;

        // Post-render attachments
        if (step === 5) {
            registerTokenListeners();
        } else if (step === 6) {
            drawVectorChart();
            registerVectorViewListener(data.vector.values);
            registerVerseVectorListeners(data.results);
        } else if (step === 7) {
            registerVerseVectorListeners(data.results);
        }
    }

    // Render Sub-steps functions
    function renderStep1RawDoc() {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-database me-2"></i>Langkah 1: Raw Document</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Representasi dokumen mentah (corpus) Al-Quran yang digunakan dalam sistem:</p>
                    
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped align-middle mb-3" style="font-size: 0.85rem;">
                            <thead class="table-light text-dark">
                                <tr>
                                    <th style="width: 40%;">Atribut</th>
                                    <th>Nilai / Detail</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Nama Corpus</strong></td>
                                    <td>Al-Quran Terjemahan Kemenag RI</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Surah</strong></td>
                                    <td>114 Surah</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Ayat</strong></td>
                                    <td>6.236 Ayat</td>
                                </tr>
                                <tr>
                                    <td><strong>Bahasa</strong></td>
                                    <td>Induk (Arab) & Terjemahan (Bahasa Indonesia)</td>
                                </tr>
                                <tr>
                                    <td><strong>Penyimpanan Database</strong></td>
                                    <td>SQLite (File: <code>semantic.db</code>)</td>
                                </tr>
                                <tr>
                                    <td><strong>Tabel Dokumen</strong></td>
                                    <td><code>quran_verses</code></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Fasa Pengindeksan (Indexing Phase):</strong> Langkah awal ini memuat database Quran mentah yang berisi data teks tekstual arab serta terjemahan bahasa Indonesianya sebelum diolah ke tahap pra-pemrosesan fasa pengindeksan.
                    </div>
                </div>
            </div>`;
    }

    function renderStep2PreprocessingCorpus() {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-magic me-2"></i>Langkah 2: Pre-processing (Corpus)</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Pipeline pembersihan teks corpus sebelum pembuatan vektor kata:</p>
                    
                    <div class="list-group list-group-flush mb-3" style="font-size: 0.85rem;">
                        <div class="list-group-item px-0 py-2">
                            <span class="badge bg-primary me-2">1</span> <strong>Case Folding:</strong> Mengubah semua karakter huruf teks terjemahan menjadi huruf kecil (lowercase).
                        </div>
                        <div class="list-group-item px-0 py-2">
                            <span class="badge bg-primary me-2">2</span> <strong>Punctuation Removal:</strong> Menghapus seluruh karakter tanda baca dan simbol non-alfanumerik.
                        </div>
                        <div class="list-group-item px-0 py-2">
                            <span class="badge bg-primary me-2">3</span> <strong>Tokenization:</strong> Memotong kalimat menjadi token kata individual (pemisah spasi).
                        </div>
                        <div class="list-group-item px-0 py-2">
                            <span class="badge bg-primary me-2">4</span> <strong>Stopword Filtering:</strong> Menyaring kata umum yang tidak memiliki bobot semantik menggunakan kamus stopword bahasa Indonesia (misal: "dan", "di", "yang", "itu").
                        </div>
                    </div>
                    
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Fasa Pengindeksan (Indexing Phase):</strong> Preprocessing diterapkan secara menyeluruh pada semua teks terjemahan 6.236 ayat Quran untuk memastikan hanya kata-kata yang bersih dan bermakna semantik saja yang akan dikonversi menjadi representasi vektor.
                    </div>
                </div>
            </div>`;
    }

    function renderStep3SemanticModel() {
        const model = modelSelect.value;
        const modelLabel = modelSelect.options[modelSelect.selectedIndex].text;
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-brain me-2"></i>Langkah 3: Single-View Semantic</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Model representasi kata semantik tunggal yang aktif digunakan:</p>
                    
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped align-middle mb-3" style="font-size: 0.85rem;">
                            <thead class="table-light text-dark">
                                <tr>
                                    <th style="width: 40%;">Spesifikasi</th>
                                    <th>Detail Konfigurasi</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Model Terpilih</strong></td>
                                    <td><span class="text-primary fw-bold">${modelLabel}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Dimensi Vektor</strong></td>
                                    <td>200 Dimensi</td>
                                </tr>
                                <tr>
                                    <td><strong>Kosakata (Vocabulary)</strong></td>
                                    <td>Kata unik yang terdaftar pada file model terkompresi (.bin/.model)</td>
                                </tr>
                                <tr>
                                    <td><strong>Fitur Khusus Model</strong></td>
                                    <td>
                                        ${model === 'word2vec' ? 'Menangkap relasi semantik lokal berdasarkan jendela kata (sliding window).' : ''}
                                        ${model === 'fasttext' ? 'Menangani kata di luar kamus (Out-of-Vocabulary/OOV) dengan pemodelan n-gram sub-kata.' : ''}
                                        ${model === 'glove' ? 'Fokus pada statistik co-occurrence global kata untuk memahami hubungan makna luas.' : ''}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Fasa Pengindeksan (Indexing Phase):</strong> Model embedding kata bertanggung jawab memberikan nilai representasi vektor numerik 200 dimensi ke setiap kata unik, di mana kata dengan konteks serupa berada berdekatan dalam ruang vektor.
                    </div>
                </div>
            </div>`;
    }

    function renderStep4IndexedDoc() {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-folder-open me-2"></i>Langkah 4: Indexed Document</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Detail status penyimpanan indeks vektor dokumen ayat Al-Quran:</p>
                    
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped align-middle mb-3" style="font-size: 0.85rem;">
                            <thead class="table-light text-dark">
                                <tr>
                                    <th style="width: 40%;">Metrik Indeks</th>
                                    <th>Detail Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Tabel Indeks Vektor</strong></td>
                                    <td><code>verse_vectors</code> (SQLite)</td>
                                </tr>
                                <tr>
                                    <td><strong>Total Vektor Terindeks</strong></td>
                                    <td>6.236 Vektor (100% Ayat Terpenuhi)</td>
                                </tr>
                                <tr>
                                    <td><strong>Status Caching</strong></td>
                                    <td><span class="badge bg-success">MEM-CACHE READY</span> (Dimuat langsung ke RAM untuk efisiensi eksekusi)</td>
                                </tr>
                                <tr>
                                    <td><strong>Waktu Pencarian Rata-rata</strong></td>
                                    <td>&lt; 5 milidetik (Direct Memory Scan)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="card mb-3 border-secondary-subtle">
                        <div class="card-header bg-light small fw-bold text-dark"><i class="fas fa-cube me-1 text-primary"></i>Konseptual: Vektor vs Matriks</div>
                        <div class="card-body small text-muted py-2" style="font-size:0.78rem; line-height:1.45;">
                            Setiap ayat disimpan sebagai <strong>vektor tunggal berdimensi 200</strong> (1D array berisi 200 angka desimal, bukan matriks 200x200). Sementara seluruh 6.236 ayat disatukan dalam memori sebagai sebuah <strong>Matriks Korpus</strong> berukuran <strong>6.236 &times; 200</strong>.
                        </div>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Akhir Fasa Pengindeksan:</strong> Seluruh ayat telah diubah menjadi vektor berdimensi 200 menggunakan model embedding pilihan, dan diindeks secara permanen. Indeks ini siap dibandingkan dengan kueri pencarian pada **Fasa Pencarian (Searching Phase)**.
                    </div>
                </div>
            </div>`;
    }

    function renderStep5Query(preprocessing) {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-keyboard me-2"></i>Langkah 5: Kueri & Pra-pemrosesan Kueri</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Kueri pencarian dibersihkan secara real-time sebelum dikonversi menjadi vektor:</p>
                    
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped align-middle mb-2" style="font-size: 0.84rem;">
                            <thead class="table-light text-dark">
                                <tr>
                                    <th style="width: 35%;">Tahap Proses</th>
                                    <th>Kondisi Teks / Data</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>1. Teks Kueri Mentah</strong></td>
                                    <td><span class="text-danger fw-bold">"${preprocessing.raw}"</span></td>
                                </tr>
                                <tr>
                                    <td><strong>2. Lowercase</strong></td>
                                    <td>"${preprocessing.lowercased}"</td>
                                </tr>
                                <tr>
                                    <td><strong>3. Hapus Tanda Baca</strong></td>
                                    <td>"${preprocessing.no_punctuation}"</td>
                                </tr>
                                <tr>
                                    <td><strong>4. Tokenisasi Kata</strong></td>
                                    <td><code class="text-primary">${JSON.stringify(preprocessing.tokens)}</code></td>
                                </tr>
                                <tr>
                                    <td><strong>5. Filter Stopwords & Bobot</strong></td>
                                    <td>
                                        <div class="d-flex flex-wrap gap-2">
                                            ${preprocessing.filtered_tokens.map(t => {
                                                const w = state.tokenWeights[t] || 1.0;
                                                return `
                                                    <div class="input-group input-group-sm d-inline-flex" style="width: auto; max-width: 145px;">
                                                        <span class="input-group-text bg-primary-subtle text-primary border-primary-subtle token-badge-click" data-token="${t}" style="cursor: pointer;" title="Klik untuk lihat sinonim">${t}</span>
                                                        <input type="number" class="form-control token-weight-input border-primary-subtle" data-token="${t}" value="${w}" min="0.1" max="10.0" step="0.1" style="width: 55px; padding: 2px 4px; font-size: 0.75rem; text-align: center;">
                                                    </div>
                                                `;
                                            }).join("")}
                                        </div>
                                        ${preprocessing.filtered_tokens.length === 0 ? '<span class="text-muted small">Kosong</span>' : ''}
                                        <p class="small text-muted mt-2 mb-0" style="font-size: 0.73rem;"><i class="fas fa-info-circle me-1"></i> Klik nama token untuk sinonim. Sesuaikan bobot token kata untuk mempengaruhi kueri (klik Simulasikan kembali untuk menerapkan).</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>`;
    }

    function renderStep6Similarity(vector, results) {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-2"><i class="fas fa-calculator me-2"></i>Langkah 6: Perhitungan Cosine Similarity</h5>
                <div class="flex-grow-1 overflow-auto">
                    <div class="row g-2 mb-2 text-center" style="font-size: 0.8rem;">
                        <div class="col-6">
                            <div class="p-1 bg-light rounded border border-secondary-subtle">
                                <span class="text-muted small" style="font-size: 0.72rem;">Dimensi Vektor</span>
                                <h6 class="text-primary mb-0 fw-bold">${vector.dimensions}d</h6>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-1 bg-light rounded border border-secondary-subtle">
                                <span class="text-muted small" style="font-size: 0.72rem;">Magnitudo L2</span>
                                <h6 class="text-success mb-0 fw-bold">${vector.magnitude.toFixed(4)}</h6>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Chart area -->
                    <div class="mb-2" style="height: 220px; position: relative;">
                        <canvas id="vectorSpaceChart"></canvas>
                    </div>

                    <!-- Vector Preview -->
                    <div class="mb-3 p-2 bg-light rounded border border-secondary-subtle" style="font-size: 0.75rem;">
                        <span class="fw-bold text-dark"><i class="fas fa-project-diagram me-1 text-primary"></i>Vektor Kueri (${vector.dimensions} dimensi):</span>
                        <div class="mt-1 font-monospace text-muted text-truncate" style="background: #ffffff; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 0.72rem;" id="vector-values-preview">
                            [${vector.values.slice(0, 10).map(v => v.toFixed(6)).join(", ")}${vector.values.length > 10 ? ', ...' : ''}]
                        </div>
                        <div class="text-end mt-1">
                            <button type="button" class="btn btn-link btn-sm p-0 text-decoration-none" id="btn-show-full-vector" style="font-size: 0.7rem;">
                                <i class="fas fa-external-link-alt me-1"></i>Lihat Seluruh Dimensi
                            </button>
                        </div>
                    </div>

                    <!-- Cosine Similarity scores -->
                    <p class="small text-secondary mb-1">Top 5 ayat kemiripan kosinus mentah tertinggi:</p>
                    <div class="table-responsive" style="max-height: 100px;">
                        <table class="table table-striped table-hover align-middle mb-0" style="font-size: 0.75rem;">
                            <thead class="table-light">
                                <tr>
                                    <th class="py-1">Ref Ayat</th>
                                    <th class="py-1">Nama Surah</th>
                                    <th class="py-1">Skor Kemiripan</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${results.slice(0, 5).map((r, idx) => `
                                    <tr>
                                        <td class="py-1">
                                            <strong>${r.surah_number}:${r.ayat_number}</strong>
                                            <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-verse-vector" data-index="${idx}" data-table="raw" title="Lihat Vektor">
                                                <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                            </button>
                                        </td>
                                        <td class="py-1">${r.surah_name}</td>
                                        <td class="py-1"><span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle font-monospace">${r.similarity.toFixed(4)}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-1 px-2 small mt-2 mb-0" style="font-size: 0.72rem;">
                        <i class="fas fa-info-circle me-1"></i> Perhitungan kemiripan dihitung antara kueri (titik biru pada plot SVD di atas) dengan seluruh vektor dokumen terindeks (titik hijau).
                    </div>
                </div>
            </div>`;
    }

    function renderStep7Results(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold);
        const filteredRefs = filtered.map(r => `${r.surah_number}:${r.ayat_number}`);
        
        // TP: in filtered AND in ground truth
        const tp = state.groundTruth.filter(v => filteredRefs.includes(v));
        // FP: in filtered BUT NOT in ground truth
        const fp = filteredRefs.filter(v => !state.groundTruth.includes(v));
        // FN: in ground truth BUT NOT in filtered
        const fn = state.groundTruth.filter(v => !filteredRefs.includes(v));

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-2"><i class="fas fa-poll me-2"></i>Langkah 7: Hasil Penyaringan & Validasi</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary mb-1">Hasil penyaringan skor kemiripan &ge; <span class="text-danger fw-bold">${state.threshold.toFixed(2)}</span>:</p>
                    
                    <div class="row g-2 mb-2 text-center" style="font-size: 0.75rem;">
                        <div class="col-4">
                            <div class="p-1 bg-light rounded border border-success">
                                <span class="badge bg-success" style="font-size: 0.65rem;">True Positive (TP)</span>
                                <h6 class="mt-1 mb-0 fw-bold text-success">${tp.length}</h6>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-1 bg-light rounded border border-warning">
                                <span class="badge bg-warning text-dark" style="font-size: 0.65rem;">False Positive (FP)</span>
                                <h6 class="mt-1 mb-0 fw-bold text-warning">${fp.length}</h6>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-1 bg-light rounded border border-danger">
                                <span class="badge bg-danger" style="font-size: 0.65rem;">False Negative (FN)</span>
                                <h6 class="mt-1 mb-0 fw-bold text-danger">${fn.length}</h6>
                            </div>
                        </div>
                    </div>

                    <div class="table-responsive" style="max-height: 120px; margin-bottom: 5px;">
                        <table class="table table-striped table-hover align-middle mb-0" style="font-size: 0.75rem;">
                            <thead class="table-light">
                                <tr>
                                    <th class="py-1">Ayat</th>
                                    <th class="py-1">Skor</th>
                                    <th class="py-1">Klasifikasi</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filtered.slice(0, 5).map((r, idx) => {
                                    const ref = `${r.surah_number}:${r.ayat_number}`;
                                    const isTp = state.groundTruth.includes(ref);
                                    return `
                                        <tr class="${isTp ? 'table-success' : 'table-warning'}" style="--bs-table-bg: ${isTp ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)'};">
                                            <td class="py-1">
                                                <strong>${ref}</strong>
                                                <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-verse-vector" data-index="${idx}" data-table="filtered" title="Lihat Vektor">
                                                    <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                                </button>
                                            </td>
                                            <td class="py-1 font-monospace">${r.similarity.toFixed(4)}</td>
                                            <td class="py-1">${isTp ? '<span class="text-success fw-bold">TP (Relevan)</span>' : '<span class="text-warning fw-bold">FP (Tidak Relevan)</span>'}</td>
                                        </tr>
                                    `;
                                }).join("")}
                                ${filtered.length === 0 ? '<tr><td colspan="3" class="text-center text-muted py-2">Tidak ada ayat lolos filter</td></tr>' : ''}
                            </tbody>
                        </table>
                    </div>
                    <div style="font-size: 0.72rem; line-height: 1.4;">
                        <strong>FN (Gagal Terambil):</strong> ${formatGroundTruthBadges(fn, "danger")}
                    </div>
                </div>
            </div>`;
    }

    function renderStep8Performance(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold).map(r => `${r.surah_number}:${r.ayat_number}`);
        
        const tp = state.groundTruth.filter(v => filtered.includes(v)).length;
        const fp = filtered.filter(v => !state.groundTruth.includes(v)).length;
        const fn = state.groundTruth.filter(v => !filtered.includes(v)).length;

        // Metrik calculations
        const precision = (tp + fp) > 0 ? tp / (tp + fp) : 0.0;
        const recall = (tp + fn) > 0 ? tp / (tp + fn) : 0.0;
        const f1 = (precision + recall) > 0 ? 2 * (precision * recall) / (precision + recall) : 0.0;

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-chart-pie me-2"></i>Langkah 8: Evaluasi Metrik Akhir</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Skor metrik performa akhir hasil kalkulasi dari fasa pencarian:</p>
                    
                    <div class="row g-2 mb-3 text-center">
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-info">
                                <h6 class="text-muted small" style="font-size: 0.75rem;">Precision</h6>
                                <h4 class="text-info mb-0 fw-bold">${(precision * 100).toFixed(1)}%</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-info">
                                <h6 class="text-muted small" style="font-size: 0.75rem;">Recall</h6>
                                <h4 class="text-info mb-0 fw-bold">${(recall * 100).toFixed(1)}%</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-warning">
                                <h6 class="text-muted small" style="font-size: 0.75rem;">F1-Score</h6>
                                <h4 class="text-warning mb-0 fw-bold">${(f1 * 100).toFixed(1)}%</h4>
                            </div>
                        </div>
                    </div>

                    <h6 class="fw-bold fs-6">Formula Perhitungan Aktif:</h6>
                    <div class="math-formula text-start mb-2" style="font-size: 0.75rem; padding: 10px; line-height: 1.5; font-weight: normal;">
                        Precision = TP / (TP + FP) = ${tp} / (${tp} + ${fp}) = <strong class="text-primary">${precision.toFixed(4)}</strong><br>
                        Recall = TP / (TP + FN) = ${tp} / (${tp} + ${fn}) = <strong class="text-primary">${recall.toFixed(4)}</strong><br>
                        F1-Score = 2 * (P * R) / (P + R) = <strong class="text-success">${f1.toFixed(4)}</strong>
                    </div>
                </div>
            </div>`;
    }
});
