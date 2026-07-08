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
        flowArrows.forEach(arrow => arrow.classList.remove("active"));

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
            simulateBtn.innerHTML = '<i class="fas fa-play me-1"></i>Simulasikan';
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

        // Update arrows UI classes
        flowArrows.forEach(arrow => {
            const arrowIndex = parseInt(arrow.dataset.arrow);
            if (arrowIndex < stepIndex) {
                arrow.classList.add("active");
            } else {
                arrow.classList.remove("active");
            }
        });

        renderActiveStep();
    }

    // Highlight active flow indicators
    function highlightFlowchart(active) {
        flowNodes.forEach(node => {
            if (active && parseInt(node.dataset.step) <= state.activeStep) {
                node.style.borderColor = "#3b82f6";
            } else {
                node.style.borderColor = "";
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
                html = renderStep3Vector(data.vector);
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
        }
    }

    // Render Sub-steps functions
    function renderStep1Input() {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-sliders-h me-2"></i>Langkah 1: Parameter Masukan</h5>
                <div class="flex-grow-1">
                    <p class="small text-secondary">Parameter aktif saat ini yang digunakan dalam simulasi pencarian:</p>
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item px-0">
                            <strong>Query Teks:</strong> <span class="text-primary fw-bold">"${state.activeQueryText || 'Belum dipilih'}"</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Model Embedding:</strong> <span class="text-primary">${modelSelect.options[modelSelect.selectedIndex].text}</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Threshold Kemiripan:</strong> <span class="badge bg-success">${state.threshold.toFixed(2)}</span>
                        </li>
                        <li class="list-group-item px-0">
                            <strong>Ground Truth Ayat (Relevan):</strong>
                            <div class="mt-2">
                                ${formatGroundTruthBadges(state.groundTruth, "primary")}
                            </div>
                        </li>
                    </ul>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis mt-3 py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Kueri aktif adalah teks pencarian yang akan dianalisis. Ground Truth adalah kumpulan ayat relevan yang telah diinput sebelumnya oleh pakar sebagai acuan kebenaran untuk menghitung metrik performa.
                    </div>
                </div>
            </div>`;
    }

    function renderStep2Preprocess(preprocessing) {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-magic me-2"></i>Langkah 2: Pra-pemrosesan Teks</h5>
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
                                        <p class="small text-muted mt-2 mb-0"><i class="fas fa-info-circle me-1"></i> Klik nama token untuk melihat sinonim terdekat. Ubah angka untuk merubah bobot kata kueri (klik Simulasikan kembali untuk menerapkan).</p>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis mt-2 py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Pra-pemrosesan teks (Preprocessing) adalah tahap pembersihan teks. Huruf diubah menjadi lowercase, tanda baca dibuang, teks dipecah menjadi unit kata (Tokenisasi), dan kata-kata umum yang tidak membawa makna khusus (Stopwords) disaring keluar.
                    </div>
                </div>
            </div>`;
    }

    function renderStep3Vector(vector) {
        const miniValues = vector.values ? vector.values.slice(0, 5) : [];
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-project-diagram me-2"></i>Langkah 3: Ekstraksi Vektor Kueri</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary mb-2">Model merata-ratakan vektor token kueri untuk menghasilkan <strong>vektor kueri 200-dimensi</strong>:</p>
                    
                    <div class="row text-center mb-2">
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border border-secondary-subtle">
                                <h6 class="text-muted mb-0 small">Dimensi Vektor</h6>
                                <h5 class="text-primary mb-0 fw-bold">${vector.dimensions}d</h5>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border border-secondary-subtle">
                                <h6 class="text-muted mb-0 small">Magnitudo (Norm-L2)</h6>
                                <h5 class="text-success mb-0 fw-bold">${vector.magnitude.toFixed(4)}</h5>
                            </div>
                        </div>
                    </div>
                    
                    <div style="height: 190px; position: relative;">
                        <canvas id="vectorSpaceChart"></canvas>
                    </div>

                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small mt-2 mb-0">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Model representasi vektor (Embedding) mengubah setiap token kata menjadi vektor numerik berdimensi 200. Vektor kueri akhir didapatkan dengan merata-ratakan seluruh vektor kata tersebut, kemudian dinormalisasi dengan L2-normalization agar panjangnya (magnitudo) bernilai 1.0. Proyeksi 2D di atas dihitung dengan Singular Value Decomposition (SVD).
                    </div>
                </div>
            </div>`;
    }

    function renderStep4Similarity(results) {
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-calculator me-2"></i>Langkah 4: Perhitungan Cosine Similarity</h5>
                <div class="flex-grow-1 overflow-auto">
                    <div class="math-formula text-primary mb-2">
                        Similarity = (A · B) / (||A|| ||B||)
                    </div>
                    <p class="small text-secondary mb-2">Skor kemiripan dihitung antara vektor kueri (A) dengan vektor tiap ayat (B) sebelum disaring:</p>
                    
                    <div class="table-responsive" style="max-height: 200px;">
                        <table class="table table-striped table-hover align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Ref Ayat</th>
                                    <th>Nama Surah</th>
                                    <th>Skor Kemiripan</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${results.slice(0, 10).map(r => `
                                    <tr>
                                        <td><strong>${r.surah_number}:${r.ayat_number}</strong></td>
                                        <td>${r.surah_name}</td>
                                        <td><span class="badge bg-warning-subtle text-warning-emphasis border border-warning-subtle font-monospace">${r.similarity.toFixed(4)}</span></td>
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                    <p class="small text-muted mt-1 mb-2">*Menampilkan top 10 ayat kemiripan tertinggi sebelum penyaringan threshold.</p>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Cosine Similarity mengukur sudut kosinus antara vektor kueri (A) dan vektor ayat (B). Nilai positif mendekati 1.0 berarti makna kueri dan ayat sangat mirip. Rumus ini menghitung perkalian titik dibagi hasil kali magnitudo kedua vektor.
                    </div>
                </div>
            </div>`;
    }

    function renderStep5Filter(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold);
        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-filter me-2"></i>Langkah 5: Penyaringan Threshold</h5>
                <div class="flex-grow-1 overflow-auto">
                    <p class="small text-secondary">Menyaring ayat hasil perhitungan kemiripan yang memiliki nilai kemiripan $\\ge$ threshold aktif (<span class="text-danger fw-bold">${state.threshold.toFixed(2)}</span>):</p>
                    
                    <div class="row text-center mb-3">
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border">
                                <h6 class="text-muted mb-1 small font-monospace">Total Ayat Masuk</h6>
                                <h4 class="text-primary mb-0 fw-bold">${results.length}</h4>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-2 bg-light rounded border">
                                <h6 class="text-muted mb-1 small font-monospace">Lolos Filter</h6>
                                <h4 class="text-success mb-0 fw-bold">${filtered.length}</h4>
                            </div>
                        </div>
                    </div>

                    <div class="table-responsive" style="max-height: 180px; margin-bottom: 10px;">
                        <table class="table table-striped table-hover align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Ref Ayat</th>
                                    <th>Skor</th>
                                    <th>Keterangan</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filtered.slice(0, 10).map(r => `
                                    <tr class="table-success" style="--bs-table-bg: rgba(16, 185, 129, 0.08);">
                                        <td><strong>${r.surah_number}:${r.ayat_number}</strong></td>
                                        <td class="font-monospace">${r.similarity.toFixed(4)}</td>
                                        <td><span class="text-success fw-bold">Lolos (>= ${state.threshold.toFixed(2)})</span></td>
                                    </tr>
                                `).join("")}
                                ${filtered.length === 0 ? '<tr><td colspan="3" class="text-center text-muted">Tidak ada ayat lolos filter</td></tr>' : ''}
                            </tbody>
                        </table>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Penyaringan Threshold menentukan batas minimum kemiripan ayat untuk masuk sebagai hasil pencarian akhir. Ayat dengan nilai kemiripan di bawah batas threshold disaring keluar untuk meminimalkan hasil yang tidak relevan.
                    </div>
                </div>
            </div>`;
    }

    function renderStep6Validation(results) {
        const filtered = results.filter(r => r.similarity >= state.threshold).map(r => `${r.surah_number}:${r.ayat_number}`);
        
        // TP: in filtered AND in ground truth
        const tp = state.groundTruth.filter(v => filtered.includes(v));
        // FP: in filtered BUT NOT in ground truth
        const fp = filtered.filter(v => !state.groundTruth.includes(v));
        // FN: in ground truth BUT NOT in filtered
        const fn = state.groundTruth.filter(v => !filtered.includes(v));

        return `
            <div class="h-100 d-flex flex-column text-dark">
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-check-double me-2"></i>Langkah 6: Validasi Ground Truth</h5>
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
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Sistem mencocokkan hasil pencarian lolos filter dengan ayat acuan. **True Positive (TP)** adalah ayat relevan yang berhasil ditemukan. **False Positive (FP)** adalah ayat hasil pencarian yang tidak relevan. **False Negative (FN)** adalah ayat relevan yang gagal ditemukan.
                    </div>
                </div>
            </div>`;
    }

    function renderStep7Evaluation(results) {
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
                <h5 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-chart-pie me-2"></i>Langkah 7: Evaluasi Metrik Akhir</h5>
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
                        Precision = TP / (TP + FP) = ${tp} / (${tp} + ${fp}) = <strong class="text-primary">${precision.toFixed(4)}</strong><br>
                        Recall = TP / (TP + FN) = ${tp} / (${tp} + ${fn}) = <strong class="text-primary">${recall.toFixed(4)}</strong><br>
                        F1-Score = 2 * (P * R) / (P + R) = <strong class="text-success">${f1.toFixed(4)}</strong>
                    </div>
                    <div class="alert alert-primary border-primary-subtle bg-primary-subtle text-primary-emphasis py-2 px-3 small">
                        <i class="fas fa-info-circle me-1"></i> <strong>Panduan Penelitian:</strong> Metrik mengevaluasi keakuratan sistem. **Precision** mengukur seberapa banyak hasil yang ditemukan benar-benar relevan. **Recall** mengukur seberapa banyak total ayat relevan yang berhasil disaring. **F1-Score** adalah rata-rata harmonik dari keduanya untuk menilai performa secara keseluruhan.
                    </div>
                </div>
            </div>`;
    }
});
