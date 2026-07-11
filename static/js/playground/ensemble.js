/**
 * JS Module for Ensemble Data Playground (Academic Research Theme)
 * Manages ensemble model tracing, interactive step visualizer, and local validations.
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
    const thresholdInput = document.getElementById("similarity-threshold");
    const thresholdVal = document.getElementById("threshold-val");
    const groundTruthInput = document.getElementById("ground-truth");
    const simulateBtn = document.getElementById("btn-simulate");
    const resetBtn = document.getElementById("btn-reset");
    const detailPanel = document.getElementById("detail-panel");
    const flowNodes = document.querySelectorAll(".flow-node-rect");
    const flowArrows = document.querySelectorAll(".flow-arrow-line, #arrow-step6");

    // Ensemble Weights inputs
    const w2vWeightInput = document.getElementById("w2v-weight");
    const ftWeightInput = document.getElementById("ft-weight");
    const gloveWeightInput = document.getElementById("glove-weight");

    // Dynamic Donut Chart update based on weights
    function updateDonutChart() {
        const w2v = parseFloat(w2vWeightInput.value) || 0;
        const ft = parseFloat(ftWeightInput.value) || 0;
        const glove = parseFloat(gloveWeightInput.value) || 0;
        
        document.getElementById('w2v-weight-val').textContent = w2v.toFixed(1);
        document.getElementById('ft-weight-val').textContent = ft.toFixed(1);
        document.getElementById('glove-weight-val').textContent = glove.toFixed(1);
        
        const total = w2v + ft + glove;
        if (total === 0) {
            document.getElementById('donut-segment-w2v').setAttribute('stroke-dasharray', '0 100');
            document.getElementById('donut-segment-ft').setAttribute('stroke-dasharray', '0 100');
            document.getElementById('donut-segment-glove').setAttribute('stroke-dasharray', '0 100');
            return;
        }
        
        const pW2v = (w2v / total) * 100;
        const pFt = (ft / total) * 100;
        const pGlove = (glove / total) * 100;
        
        const segW2v = document.getElementById('donut-segment-w2v');
        segW2v.setAttribute('stroke-dasharray', `${pW2v} ${100 - pW2v}`);
        segW2v.setAttribute('stroke-dashoffset', '25');
        
        const segFt = document.getElementById('donut-segment-ft');
        segFt.setAttribute('stroke-dasharray', `${pFt} ${100 - pFt}`);
        segFt.setAttribute('stroke-dashoffset', `${25 - pW2v}`);
        
        const segGlove = document.getElementById('donut-segment-glove');
        segGlove.setAttribute('stroke-dasharray', `${pGlove} ${100 - pGlove}`);
        segGlove.setAttribute('stroke-dashoffset', `${25 - pW2v - pFt}`);
    }

    [w2vWeightInput, ftWeightInput, gloveWeightInput].forEach(input => {
        input.addEventListener("input", updateDonutChart);
    });

    // Initialize donut
    updateDonutChart();

    // Load queries on startup
    loadQueries();

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

        simulateBtn.disabled = false;
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
        document.getElementById('aggregation-method').value = 'score_fusion';

        // Reset model weights
        w2vWeightInput.value = 1.0;
        ftWeightInput.value = 1.0;
        gloveWeightInput.value = 1.0;
        updateDonutChart();

        // Reset flowchart step active status
        highlightFlowchart(false);
        flowNodes.forEach(node => node.classList.remove("active"));
        if (flowNodes.length > 0) flowNodes[0].classList.add("active");
        flowArrows.forEach(arrow => {
            arrow.classList.remove("active");
            if (arrow.tagName === 'line' || arrow.tagName === 'path') {
                arrow.setAttribute('marker-end', 'url(#arrow-inactive)');
            }
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
            text: 'Seluruh input parameter dan data simulasi ensemble telah dibersihkan.',
            timer: 1500,
            showConfirmButton: false
        });
    });

    // Run search simulation
    async function runSimulation() {
        if (!state.activeQueryText) return;

        const w2vW = parseFloat(w2vWeightInput.value) || 1.0;
        const ftW = parseFloat(ftWeightInput.value) || 1.0;
        const gloveW = parseFloat(gloveWeightInput.value) || 1.0;
        
        simulateBtn.disabled = true;
        simulateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        try {
            const response = await fetch("/api/playground/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query_text: state.activeQueryText,
                    model_type: 'ensemble',
                    aggregation_method: document.getElementById('aggregation-method').value,
                    token_weights: state.tokenWeights,
                    model_weights: {
                        word2vec: w2vW,
                        fasttext: ftW,
                        glove: gloveW
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                state.simulationData = data;
                
                // Highlight flow node paths
                highlightFlowchart(true);
                
                // Advance to Step 2 (Pra-pemrosesan Teks)
                changeStep(2);
                
                Swal.fire({
                    icon: 'success',
                    title: 'Simulasi Selesai',
                    text: 'Jelajahi alur logika bisnis melalui menu Alur Eksekusi di kanan!',
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
            simulateBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }

    // Step switching logic with safety guard
    function changeStep(stepIndex) {
        if (stepIndex > 1 && !state.simulationData) {
            Swal.fire({
                icon: "info",
                title: "Belum Ada Simulasi",
                text: "Silakan tekan tombol 'Simulasikan' terlebih dahulu sebelum melihat langkah ini.",
                timer: 2000,
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

        // Update arrows UI classes and SVG markers
        flowArrows.forEach(arrow => {
            const arrowIndex = parseInt(arrow.dataset.arrow);
            if (arrowIndex < stepIndex) {
                arrow.classList.add("active");
                if (arrow.tagName === 'line' || arrow.tagName === 'path') {
                    arrow.setAttribute('marker-end', 'url(#arrow-active)');
                }
            } else {
                arrow.classList.remove("active");
                if (arrow.tagName === 'line' || arrow.tagName === 'path') {
                    arrow.setAttribute('marker-end', 'url(#arrow-inactive)');
                }
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
            } else {
                if (step !== 1) {
                    node.classList.remove("active");
                }
            }
        });
    }

    // Parser for Ground Truth strings
    function parseGroundTruth(inputVal) {
        if (!inputVal) return [];
        return inputVal.split(",")
            .map(v => v.trim())
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
                const model = 'ensemble';

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
                                <span class="badge bg-info-subtle text-info-emphasis">${n.similarity.toFixed(4)}</span>
                            </li>
                        `).join("");

                        Swal.fire({
                            title: `<i class="fas fa-search me-2 text-info"></i>Sinonim Kata (Ensemble): "${token}"`,
                            html: `
                                <p class="small text-muted text-start mb-2">10 kata terdekat berdasarkan kedekatan rata-rata model W2V, FT, dan GloVe:</p>
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
                    title: '<i class="fas fa-vector-square me-2 text-info"></i>Representasi Vektor Kueri (Ensemble)',
                    html: `
                        <p class="small text-muted text-start mb-2">Nilai numerik untuk seluruh <strong>${values.length} dimensi</strong> kueri gabungan (L2 Normalized):</p>
                        <div class="vector-grid bg-dark p-2 rounded text-start">
                            ${formattedValues}
                        </div>
                    `,
                    width: '650px',
                    showDenyButton: true,
                    showCancelButton: false,
                    confirmButtonText: 'Tutup',
                    denyButtonText: '<i class="fas fa-download me-1"></i> Download JSON',
                    denyButtonColor: '#0dcaf0'
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
            model_type: 'ensemble',
            dimensions: values.length,
            vector: values
        }, null, 2);
        
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const safeQuery = state.activeQueryText.toLowerCase().replace(/[^\w\-]/g, '_');
        a.download = `vector_query_ensemble_${safeQuery}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function registerVerseVectorListeners(results) {
        document.querySelectorAll(".btn-show-verse-vector").forEach(btn => {
            btn.addEventListener("click", () => {
                const index = parseInt(btn.dataset.index);
                const tableType = btn.dataset.table;
                
                let verse;
                if (tableType === "ensemble") {
                    const ensembleSorted = results.slice(0, 5);
                    verse = ensembleSorted[index];
                } else if (tableType === "passed") {
                    const passed = results.filter(r => r.similarity >= state.threshold && r.model_count >= 2);
                    verse = passed[index];
                } else if (tableType === "failed") {
                    const failedVoting = results.filter(r => r.similarity >= state.threshold && r.model_count < 2);
                    verse = failedVoting[index];
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
            title: `<i class="fas fa-vector-square me-2 text-success"></i>Vektor Ayat ${verse.surah_number}:${verse.ayat_number} (Ensemble)`,
            html: `
                <p class="small text-muted text-start mb-2">Nilai numerik untuk seluruh <strong>${values.length} dimensi</strong> ayat (${verse.surah_name}) hasil rerata terbobot:</p>
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
            model_type: 'ensemble',
            dimensions: verse.vector_values.length,
            vector: verse.vector_values
        }, null, 2);
        
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `vector_verse_${verse.surah_number}_${verse.ayat_number}_ensemble.json`;
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
                label: 'Kueri Gabungan: ' + state.activeQueryText,
                data: [{ x: queryPoint.x, y: queryPoint.y }],
                backgroundColor: '#0dcaf0',
                borderColor: '#0aa2c0',
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
                                    return 'Kueri Gabungan';
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
        if (!state.simulationData && state.activeStep > 1) {
            state.activeStep = 1;
        }

        if (state.activeStep === 1) {
            detailPanel.innerHTML = renderStep1Input();
            return;
        }

        const data = state.simulationData;
        const step = state.activeStep;
        
        let html = "";
        
        switch(step) {
            case 2:
                html = renderStep2Preprocess(data.preprocessing);
                break;
            case 3:
                html = renderStep3Vector(data.vector, data.ensemble_sub_vectors);
                break;
            case 4:
                html = renderStep4Similarity(data.results);
                break;
            case 5:
                html = renderStep5Filter(data.results);
                break;
            case 6:
                html = renderStep6Validation(data.results);
                break;
            case 7:
                html = renderStep7Evaluation(data.results);
                break;
            default:
                html = "<h5>Langkah tidak dikenali</h5>";
        }
        
        detailPanel.innerHTML = html;

        // Post-render attachments
        if (step === 2) {
            registerTokenListeners();
        } else if (step === 3) {
            drawVectorChart();
            registerVectorViewListener(data.vector.values);
            registerSubVectorListeners(data.ensemble_sub_vectors);
        } else if (step === 4) {
            registerVerseVectorListeners(data.results);
        } else if (step === 5) {
            registerVerseVectorListeners(data.results);
        }
    }

    function registerSubVectorListeners(subVectors) {
        document.querySelectorAll(".btn-show-sub-vector").forEach(btn => {
            btn.addEventListener("click", () => {
                const model = btn.dataset.model;
                const values = subVectors[model];
                if (values) {
                    showSubVectorModal(model, values);
                }
            });
        });
    }

    function showSubVectorModal(modelName, values) {
        const formattedValues = values.map((v, i) => `
            <div class="vector-cell" title="Dimensi ${i+1}: ${v}">
                <span class="dim-label">d${i+1}</span>
                <span class="dim-val">${v.toFixed(5)}</span>
            </div>
        `).join("");

        const titleMap = {
            'word2vec': 'Word2Vec',
            'fasttext': 'FastText',
            'glove': 'GloVe'
        };

        const colorMap = {
            'word2vec': '#3b82f6',
            'fasttext': '#10b981',
            'glove': '#a855f7'
        };

        Swal.fire({
            title: `<i class="fas fa-vector-square me-2" style="color: ${colorMap[modelName]}"></i>Vektor Kueri Dasar: ${titleMap[modelName]}`,
            html: `
                <p class="small text-muted text-start mb-2">Nilai numerik kueri untuk model dasar <strong>${titleMap[modelName]} (${values.length} dimensi)</strong>:</p>
                <div class="vector-grid bg-dark p-2 rounded text-start">
                    ${formattedValues}
                </div>
            `,
            width: '650px',
            showDenyButton: true,
            showCancelButton: false,
            confirmButtonText: 'Tutup',
            denyButtonText: '<i class="fas fa-download me-1"></i> Download JSON',
            denyButtonColor: colorMap[modelName]
        }).then((result) => {
            if (result.isDenied) {
                downloadSubVectorJSON(modelName, values);
            }
        });
    }

    function downloadSubVectorJSON(modelName, values) {
        const payload = JSON.stringify({
            query: state.activeQueryText,
            model_type: modelName,
            dimensions: values.length,
            vector: values
        }, null, 2);
        
        const blob = new Blob([payload], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const safeQuery = state.activeQueryText.toLowerCase().replace(/[^\w\-]/g, '_');
        a.download = `vector_query_${modelName}_${safeQuery}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Render Sub-steps functions
    function renderStep1Input() {
        const method = document.getElementById('aggregation-method').value.replace('_', ' ').toUpperCase();
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-sliders-h me-2"></i>Langkah 1: Parameter Masukan</h5>
                <div class="flex-grow-1">
                    <p class="small text-secondary">Parameter aktif saat ini yang digunakan dalam simulasi pencarian:</p>
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item px-0">
                            <strong>Query Teks:</strong> <span class="text-info fw-bold">"${state.activeQueryText || 'Belum dipilih'}"</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Model Embedding:</strong> <span class="text-info">Ensemble Model (Word2Vec + FastText + GloVe)</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Strategi Agregasi:</strong> <span class="badge bg-info">${method}</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Bobot Model:</strong>
                            <span class="badge bg-primary">W2V: ${parseFloat(w2vWeightInput.value).toFixed(1)}</span>
                            <span class="badge bg-success">FT: ${parseFloat(ftWeightInput.value).toFixed(1)}</span>
                            <span class="badge bg-purple" style="background-color: #a855f7;">GloVe: ${parseFloat(gloveWeightInput.value).toFixed(1)}</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Threshold Kemiripan:</strong> <span class="badge bg-success">${state.threshold.toFixed(2)}</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Ground Truth Ayat (Relevan):</strong>
                            <div class="mt-2">
                                ${formatGroundTruthBadges(state.groundTruth, "info")}
                            </div>
                        </li>
                    </ul>
                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis mt-3 py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Kueri aktif adalah teks pencarian yang akan dianalisis. Ground Truth adalah kumpulan ayat relevan yang telah diinput sebelumnya oleh pakar sebagai acuan kebenaran untuk menghitung metrik performa.
                    </div>
                </div>
            </div>`;
    }

    function renderStep2Preprocess(preprocessing) {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-magic me-2"></i>Langkah 2: Pra-pemrosesan Teks</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Kueri teks dibersihkan dan dipecah menjadi token kata:</p>
                    
                    <div class="table-responsive">
                        <table class="table table-bordered table-striped align-middle mb-2">
                            <thead class="table-light text-dark">
                                <tr>
                                    <th style="width: 35%;">Tahap Proses</th>
                                    <th>Kondisi Teks / Data</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>1. Teks Mentah (Raw)</strong></td>
                                    <td><span class="text-danger fw-bold">"${preprocessing.raw}"</span></td>
                                </tr>
                                <tr>
                                    <td><strong>2. Huruf Kecil (Lowercase)</strong></td>
                                    <td>"${preprocessing.lowercased}"</td>
                                </tr>
                                <tr>
                                    <td><strong>3. Hapus Tanda Baca</strong></td>
                                    <td>"${preprocessing.no_punctuation}"</td>
                                </tr>
                                <tr>
                                    <td><strong>4. Tokenisasi Kata</strong></td>
                                    <td><code class="text-info">${JSON.stringify(preprocessing.tokens)}</code></td>
                                </tr>
                                <tr>
                                    <td><strong>5. Filter Stopwords & Bobot</strong></td>
                                    <td>
                                        <div class="d-flex flex-wrap gap-2">
                                            ${preprocessing.filtered_tokens.map(t => {
                                                const w = state.tokenWeights[t] || 1.0;
                                                return `
                                                    <div class="input-group input-group-sm d-inline-flex" style="width: auto; max-width: 145px;">
                                                        <span class="input-group-text bg-info-subtle text-info border-info-subtle token-badge-click" data-token="${t}" style="cursor: pointer;" title="Klik untuk lihat sinonim">${t}</span>
                                                        <input type="number" class="form-control token-weight-input border-info-subtle" data-token="${t}" value="${w}" min="0.1" max="10.0" step="0.1" style="width: 55px; padding: 2px 4px; font-size: 0.75rem; text-align: center;">
                                                    </div>
                                                `;
                                            }).join("")}
                                        </div>
                                        ${preprocessing.filtered_tokens.length === 0 ? '<span class="text-muted small">Kosong</span>' : ''}
                                        <p class="small text-muted mt-2 mb-0"><i class="fas fa-info-circle me-1"></i> Klik nama token untuk melihat sinonim terdekat. Ubah angka untuk merubah bobot kata kueri (klik Simulasikan kembali untuk menerapkan).</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis mt-2 py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Pra-pemrosesan teks (Preprocessing) adalah tahap pembersihan teks. Huruf diubah menjadi lowercase, tanda baca dibuang, teks dipecah menjadi unit kata (Tokenisasi), dan kata-kata umum yang tidak membawa makna khusus (Stopwords) disaring keluar.
                    </div>
                </div>
            </div>`;
    }

    function renderStep3Vector(vector, subVectors) {
        const w2vW = parseFloat(w2vWeightInput.value) || 1.0;
        const ftW = parseFloat(ftWeightInput.value) || 1.0;
        const gloveW = parseFloat(gloveWeightInput.value) || 1.0;
        
        let subVectorsTableHtml = "";
        if (subVectors) {
            const w2vVal = subVectors.word2vec ? `[ ${subVectors.word2vec.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]` : '<span class="text-muted italic">Tidak tersedia (OOV)</span>';
            const ftVal = subVectors.fasttext ? `[ ${subVectors.fasttext.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]` : '<span class="text-muted italic">Tidak tersedia (OOV)</span>';
            const gloveVal = subVectors.glove ? `[ ${subVectors.glove.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]` : '<span class="text-muted italic">Tidak tersedia (OOV)</span>';
            const finalVal = `[ ${vector.values.slice(0, 5).map(v => v.toFixed(4)).join(', ')} ]`;
            
            // Calculate sample weighted average (first 5 elements)
            let avgVal5 = [0, 0, 0, 0, 0];
            const sumW = w2vW + ftW + gloveW;
            if (sumW > 0) {
                for (let i = 0; i < 5; i++) {
                    let val = 0;
                    if (subVectors.word2vec) val += subVectors.word2vec[i] * w2vW;
                    if (subVectors.fasttext) val += subVectors.fasttext[i] * ftW;
                    if (subVectors.glove) val += subVectors.glove[i] * gloveW;
                    avgVal5[i] = val / sumW;
                }
            }
            
            subVectorsTableHtml = `
                <!-- Sub vectors breakdown table -->
                <span class="text-secondary fw-semibold d-block mb-1"><i class="fas fa-sitemap me-1 text-info"></i>Kontribusi Vektor Kueri Dasar (Sampel 5 Dimensi Pertama):</span>
                <div class="table-responsive mb-3">
                    <table class="table table-sm table-bordered bg-white align-middle text-dark" style="font-size: 0.72rem; margin-bottom: 0;">
                        <thead class="table-light">
                            <tr>
                                <th>Model & Bobot Kontribusi</th>
                                <th class="font-monospace">Sampel Vektor [d1, d2, d3, d4, d5]</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    Vektor Word2Vec (Bobot: <code>${w2vW.toFixed(1)}</code>)
                                    ${subVectors.word2vec ? `
                                        <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-sub-vector" data-model="word2vec" title="Lihat Vektor Lengkap">
                                            <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                        </button>
                                    ` : ''}
                                </td>
                                <td class="font-monospace text-muted">${w2vVal}</td>
                            </tr>
                            <tr>
                                <td>
                                    Vektor FastText (Bobot: <code>${ftW.toFixed(1)}</code>)
                                    ${subVectors.fasttext ? `
                                        <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-sub-vector" data-model="fasttext" title="Lihat Vektor Lengkap">
                                            <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                        </button>
                                    ` : ''}
                                </td>
                                <td class="font-monospace text-muted">${ftVal}</td>
                            </tr>
                            <tr>
                                <td>
                                    Vektor GloVe (Bobot: <code>${gloveW.toFixed(1)}</code>)
                                    ${subVectors.glove ? `
                                        <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-sub-vector" data-model="glove" title="Lihat Vektor Lengkap">
                                            <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                        </button>
                                    ` : ''}
                                </td>
                                <td class="font-monospace text-muted">${gloveVal}</td>
                            </tr>
                            <tr class="table-info" style="--bs-table-bg: rgba(13, 202, 240, 0.08);">
                                <td><strong>Rerata Terbobot (Weighted Mean)</strong></td>
                                <td class="font-monospace text-dark fw-semibold">[ ${avgVal5.map(v => v.toFixed(4)).join(', ')} ]</td>
                            </tr>
                            <tr class="table-success" style="--bs-table-bg: rgba(25, 135, 84, 0.08);">
                                <td><strong>Hasil Akhir (L2 Normalized)</strong></td>
                                <td class="font-monospace text-success fw-bold">${finalVal}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `;
        }

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-project-diagram me-2"></i>Langkah 3: Penggabungan Vektor Kueri</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary mb-2">Model Ensemble merata-ratakan vektor kueri dari ketiga model dasar:</p>
                    
                    <div class="math-formula text-info mb-3">
                        V_avg = (w1*V_w2v + w2*V_ft + w3*V_glove) / (w1 + w2 + w3)
                    </div>

                    ${subVectorsTableHtml}

                    <div class="row text-center mb-2">
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border border-secondary-subtle">
                                <h6 class="text-muted mb-0 small">Dimensi Vektor Gabungan</h6>
                                <h5 class="text-info mb-0 fw-bold">${vector.dimensions}d</h5>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border border-secondary-subtle">
                                <h6 class="text-muted mb-0 small">Magnitudo Gabungan (L2)</h6>
                                <h5 class="text-success mb-0 fw-bold">${vector.magnitude.toFixed(4)}</h5>
                            </div>
                        </div>
                    </div>
                    
                    <div style="height: 190px; position: relative;" class="mb-2">
                        <canvas id="vectorSpaceChart"></canvas>
                    </div>
                    
                    <!-- Vector Preview -->
                    <div class="mb-2 p-2 bg-light rounded border border-secondary-subtle" style="font-size: 0.75rem;">
                        <span class="fw-bold text-dark"><i class="fas fa-project-diagram me-1 text-info"></i>Vektor Kueri (${vector.dimensions} dimensi):</span>
                        <div class="mt-1 font-monospace text-muted text-truncate" style="background: #ffffff; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 0.72rem;" id="vector-values-preview">
                            [${vector.values.slice(0, 10).map(v => v.toFixed(6)).join(", ")}${vector.values.length > 10 ? ', ...' : ''}]
                        </div>
                        <div class="text-end mt-1">
                            <button type="button" class="btn btn-link btn-sm p-0 text-decoration-none" id="btn-show-full-vector" style="font-size: 0.7rem;">
                                <i class="fas fa-external-link-alt me-1"></i>Lihat Seluruh Dimensi
                            </button>
                        </div>
                    </div>

                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis py-2 px-3 small mt-2 mb-0">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Vektor kueri gabungan dibentuk dengan merata-ratakan koordinat spasial vektor kueri dari model Word2Vec, FastText, dan GloVe secara elemen-demi-elemen berdasarkan bobot kontribusi model, lalu dinormalisasi L2.
                    </div>
                </div>
            </div>`;
    }

    function renderStep4Similarity(results) {
        const w2vSorted = [...results].sort((a,b) => (b.individual_scores?.word2vec || 0) - (a.individual_scores?.word2vec || 0)).slice(0, 5);
        const ftSorted = [...results].sort((a,b) => (b.individual_scores?.fasttext || 0) - (a.individual_scores?.fasttext || 0)).slice(0, 5);
        const gloveSorted = [...results].sort((a,b) => (b.individual_scores?.glove || 0) - (a.individual_scores?.glove || 0)).slice(0, 5);
        const ensembleSorted = results.slice(0, 5);

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-2"><i class="fas fa-calculator me-2"></i>Langkah 4: Perbandingan Multi-Similarity</h5>
                <p class="small text-secondary mb-2">Perbandingan hasil pencarian Top 5 antara model dasar individual dengan model Ensemble gabungan:</p>
                
                <div class="row g-2 flex-grow-1 overflow-auto" style="font-size: 0.72rem;">
                    <!-- Word2Vec -->
                    <div class="col-md-3">
                        <div class="card h-100 border-primary-subtle" style="background: #eff6ff;">
                            <div class="card-header bg-primary text-white p-1 text-center fw-bold" style="font-size: 0.7rem;">Word2Vec Only</div>
                            <div class="list-group list-group-flush">
                                ${w2vSorted.map(r => `
                                    <div class="list-group-item p-1 d-flex justify-content-between align-items-center bg-transparent">
                                        <strong>${r.surah_number}:${r.ayat_number}</strong>
                                        <span class="badge bg-primary">${(r.individual_scores?.word2vec || 0).toFixed(3)}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                    <!-- FastText -->
                    <div class="col-md-3">
                        <div class="card h-100 border-success-subtle" style="background: #f0fdf4;">
                            <div class="card-header bg-success text-white p-1 text-center fw-bold" style="font-size: 0.7rem;">FastText Only</div>
                            <div class="list-group list-group-flush">
                                ${ftSorted.map(r => `
                                    <div class="list-group-item p-1 d-flex justify-content-between align-items-center bg-transparent">
                                        <strong>${r.surah_number}:${r.ayat_number}</strong>
                                        <span class="badge bg-success">${(r.individual_scores?.fasttext || 0).toFixed(3)}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                    <!-- GloVe -->
                    <div class="col-md-3">
                        <div class="card h-100 border-purple-subtle" style="background: #f5f3ff;">
                            <div class="card-header text-white p-1 text-center fw-bold" style="background-color: #8b5cf6; font-size: 0.7rem;">GloVe Only</div>
                            <div class="list-group list-group-flush">
                                ${gloveSorted.map(r => `
                                    <div class="list-group-item p-1 d-flex justify-content-between align-items-center bg-transparent">
                                        <strong>${r.surah_number}:${r.ayat_number}</strong>
                                        <span class="badge bg-purple" style="background-color: #8b5cf6;">${(r.individual_scores?.glove || 0).toFixed(3)}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                    <!-- Ensemble -->
                    <div class="col-md-3">
                        <div class="card h-100 border-info-subtle shadow-sm" style="background: #ecfeff;">
                            <div class="card-header bg-info text-white p-1 text-center fw-bold" style="font-size: 0.7rem;">Ensemble Gabungan</div>
                            <div class="list-group list-group-flush">
                                ${ensembleSorted.map((r, idx) => `
                                    <div class="list-group-item p-1 d-flex justify-content-between align-items-center bg-transparent fw-bold" style="font-size: 0.7rem;">
                                        <span>
                                            <strong class="text-info">${r.surah_number}:${r.ayat_number}</strong>
                                            <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-verse-vector" data-index="${idx}" data-table="ensemble" title="Lihat Vektor">
                                                <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                            </button>
                                        </span>
                                        <span class="badge bg-warning text-dark font-monospace">${r.similarity.toFixed(3)}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis py-1 px-2 small mt-2 mb-0" style="font-size: 0.72rem;">
                    <i class="fas fa-info-circle me-1"></i> <strong>Mengapa berbeda?</strong> Word2Vec & GloVe menggunakan level-word sehingga sensitif terhadap OOV, sedangkan FastText toleran OOV. Model Ensemble menggabungkan keunggulan ketiganya.
                </div>
            </div>`;
    }

    function renderStep5Filter(results) {
        // Filter: similarity >= threshold AND model_count >= 2 (Voting filter!)
        const passed = results.filter(r => r.similarity >= state.threshold && (r.model_count >= 2));
        const failedVoting = results.filter(r => r.similarity >= state.threshold && (r.model_count < 2));

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-filter me-2"></i>Langkah 5: Penyaringan & Voting Filter</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Menyaring skor ensemble $\\ge$ <span class="text-danger fw-bold">${state.threshold.toFixed(2)}</span> dan menerapkan **Voting Filter (Kesepakatan $\\ge 2$ model)**:</p>
                    
                    <div class="row text-center mb-3">
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border">
                                <h6 class="text-muted mb-1 small font-monospace">Lolos Filter</h6>
                                <h4 class="text-success mb-0 fw-bold">${passed.length}</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border border-warning">
                                <h6 class="text-muted mb-1 small font-monospace">Gagal Voting</h6>
                                <h4 class="text-warning mb-0 fw-bold">${failedVoting.length}</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border">
                                <h6 class="text-muted mb-1 small font-monospace">Total Masuk</h6>
                                <h4 class="text-primary mb-0 fw-bold">${results.length}</h4>
                            </div>
                        </div>
                    </div>

                    <div class="table-responsive" style="max-height: 180px; margin-bottom: 10px;">
                        <table class="table table-striped table-hover align-middle mb-0" style="font-size: 0.78rem;">
                            <thead class="table-light">
                                <tr>
                                    <th>Ref Ayat</th>
                                    <th>Skor</th>
                                    <th>Model Setuju</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${passed.slice(0, 5).map((r, idx) => `
                                    <tr class="table-success" style="--bs-table-bg: rgba(16, 185, 129, 0.08);">
                                        <td>
                                            <strong>${r.surah_number}:${r.ayat_number}</strong>
                                            <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-verse-vector" data-index="${idx}" data-table="passed" title="Lihat Vektor">
                                                <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                            </button>
                                        </td>
                                        <td class="font-monospace">${r.similarity.toFixed(4)}</td>
                                        <td class="text-center">${r.model_count}</td>
                                        <td><span class="text-success fw-bold">🟢 Lolos</span></td>
                                    </tr>
                                `).join("")}
                                ${failedVoting.slice(0, 5).map((r, idx) => `
                                    <tr class="table-warning" style="--bs-table-bg: rgba(255, 193, 7, 0.08);">
                                        <td>
                                            <strong>${r.surah_number}:${r.ayat_number}</strong>
                                            <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-verse-vector" data-index="${idx}" data-table="failed" title="Lihat Vektor">
                                                <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                            </button>
                                        </td>
                                        <td class="font-monospace">${r.similarity.toFixed(4)}</td>
                                        <td class="text-center">${r.model_count}</td>
                                        <td><span class="text-warning fw-bold">❌ Saring Out (Model < 2)</span></td>
                                    </tr>
                                `).join("")}
                                ${passed.length === 0 && failedVoting.length === 0 ? '<tr><td colspan="4" class="text-center text-muted">Tidak ada ayat lolos filter</td></tr>' : ''}
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Voting Filter adalah benteng keakuratan Ensemble. Ayat yang hanya dideteksi oleh 1 model dasar akan disaring keluar (didiskualifikasi) untuk menjaga konsistensi makna.
                    </div>
                </div>
            </div>`;
    }

    function renderStep6Validation(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold && r.model_count >= 2).map(r => `${r.surah_number}:${r.ayat_number}`);
        
        const tp = state.groundTruth.filter(v => filtered.includes(v));
        const fp = filtered.filter(v => !state.groundTruth.includes(v));
        const fn = state.groundTruth.filter(v => !filtered.includes(v));

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-check-double me-2"></i>Langkah 6: Validasi Ground Truth</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Sistem membandingkan hasil pencarian lolos filter dengan ayat acuan (*Ground Truth*) untuk menghitung keakuratan:</p>
                    
                    <div class="row g-2 mb-3 text-center">
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border border-success">
                                <span class="badge bg-success text-white">True Positive</span>
                                <h4 class="mt-2 mb-0 fw-bold text-success">${tp.length}</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border border-warning">
                                <span class="badge bg-warning text-dark">False Positive</span>
                                <h4 class="mt-2 mb-0 fw-bold text-warning">${fp.length}</h4>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-2 bg-light rounded border border-danger">
                                <span class="badge bg-danger text-white">False Negative</span>
                                <h4 class="mt-2 mb-0 fw-bold text-danger">${fn.length}</h4>
                            </div>
                        </div>
                    </div>

                    <h6 class="fw-bold fs-6">Rincian Pengelompokan:</h6>
                    <div style="font-size: 0.88rem; line-height: 1.8; margin-bottom: 10px;">
                        <div class="mb-2">
                            <span class="text-success fw-bold">🟢 True Positive (TP):</span>
                            <div class="mt-1">${formatGroundTruthBadges(tp, "success")}</div>
                        </div>
                        <div class="mb-2">
                            <span class="text-warning fw-bold">🟡 False Positive (FP):</span>
                            <div class="mt-1">${formatGroundTruthBadges(fp, "warning")}</div>
                        </div>
                        <div class="mb-2">
                            <span class="text-danger fw-bold">🔴 False Negative (FN):</span>
                            <div class="mt-1">${formatGroundTruthBadges(fn, "danger")}</div>
                        </div>
                    </div>
                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Hasil di atas didasarkan pada ayat yang lolos **Ensemble Threshold** DAN disetujui minimal oleh 2 model dasar.
                    </div>
                </div>
            </div>`;
    }

    function renderStep7Evaluation(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold && r.model_count >= 2).map(r => `${r.surah_number}:${r.ayat_number}`);
        
        const tp = state.groundTruth.filter(v => filtered.includes(v)).length;
        const fp = filtered.filter(v => !state.groundTruth.includes(v)).length;
        const fn = state.groundTruth.filter(v => !filtered.includes(v)).length;

        const precision = (tp + fp) > 0 ? tp / (tp + fp) : 0.0;
        const recall = (tp + fn) > 0 ? tp / (tp + fn) : 0.0;
        const f1 = (precision + recall) > 0 ? 2 * (precision * recall) / (precision + recall) : 0.0;

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-info border-bottom pb-2 mb-3"><i class="fas fa-chart-pie me-2"></i>Langkah 7: Evaluasi Metrik Akhir</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Skor metrik performa akhir hasil kalkulasi dari data validasi sebelumnya:</p>
                    
                    <div class="row g-2 mb-3 text-center">
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-info">
                                <h6 class="text-muted small">Precision</h6>
                                <h3 class="text-info mb-0 fw-bold">${(precision * 100).toFixed(1)}%</h3>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-info">
                                <h6 class="text-muted small">Recall</h6>
                                <h3 class="text-info mb-0 fw-bold">${(recall * 100).toFixed(1)}%</h3>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="p-3 bg-light rounded border border-warning">
                                <h6 class="text-muted small">F1-Score</h6>
                                <h3 class="text-warning mb-0 fw-bold">${(f1 * 100).toFixed(1)}%</h3>
                            </div>
                        </div>
                    </div>

                    <h6 class="fw-bold fs-6">Rincian Formula Perhitungan:</h6>
                    <div class="math-formula text-start mb-2" style="font-size: 0.78rem; padding: 12px; line-height: 1.6; font-weight: normal;">
                        Precision = TP / (TP + FP) = ${tp} / (${tp} + ${fp}) = <strong class="text-info">${precision.toFixed(4)}</strong><br>
                        Recall = TP / (TP + FN) = ${tp} / (${tp} + ${fn}) = <strong class="text-info">${recall.toFixed(4)}</strong><br>
                        F1-Score = 2 * (P * R) / (P + R) = <strong class="text-success">${f1.toFixed(4)}</strong>
                    </div>
                    <div class="alert alert-info border-info-subtle bg-info-subtle text-info-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Hasil evaluasi akhir model ensemble ini biasanya menunjukkan performa Precision dan F1-Score yang lebih stabil dibandingkan single model, berkat mekanisme voting filter.
                    </div>
                </div>
            </div>`;
    }
});
