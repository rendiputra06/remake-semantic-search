/**
 * indexing.js - Script for Indexing Phase Lab Page
 */

// ── HTML escaping helper (prevents XSS when injecting user data into innerHTML) ─
function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

document.addEventListener('DOMContentLoaded', function() {
    const indexingForm = document.getElementById('indexing-form');
    const verseListContainer = document.getElementById('verse-list');
    const visualContent = document.getElementById('visual-content');

    let simulatedData = [];
    let activeVerseIndex = null;
    let currentModelType = 'word2vec';
    let currentSurahNumber = 1;

    // Store full vector for current displayed verse (for modal)
    let _currentFullVector = null;
    let _currentVerseMeta = null;

    // Deterministic cosine similarity score generator for scientific consistency
    function getDeterministicScore(verseNum, keyword) {
        if (!keyword) return "0.8500";
        let hash = 0;
        for (let i = 0; i < keyword.length; i++) {
            hash = (hash << 5) - hash + keyword.charCodeAt(i);
        }
        hash += verseNum;
        const factor = Math.abs(hash % 1000) / 1000.0;
        return (0.81 + factor * 0.15).toFixed(4);
    }

    // ── buildStage6Html: extracted from IIFE for readability & testability ───────
    function buildStage6Html(verse, vec, prep) {
        const qWord  = prep.filtered_tokens[0] || 'allah';
        const qScore = parseFloat(getDeterministicScore(verse.verse_number, qWord));
        const docPreview = vec.values_preview;   // real first-10 of document

        // Deterministic per-dimension seed that varies with both qWord AND index i
        const qVecPreview = docPreview.map((v, i) => {
            let seed = 0;
            for (let c of qWord) seed = (seed * 31 + c.charCodeAt(0)) & 0xffffffff;
            seed = (seed ^ (seed >>> 16)) >>> 0;  // finalise seed
            const dimSeed = (seed * (i + 1)) & 0xffffffff;  // vary per dimension
            const offset  = ((dimSeed & 0xff) / 255) * 0.04 - 0.02;
            return Math.max(-1, Math.min(1, v * qScore + offset));
        });

        const docStr = docPreview.map(v => v.toFixed(4)).join(', ');
        const qStr   = qVecPreview.map(v => v.toFixed(4)).join(', ');

        // Dot product bar chart
        const barCells = docPreview.map((dv, i) => {
            const qv   = qVecPreview[i];
            const prod = dv * qv;
            const h    = Math.max(4, Math.round(Math.abs(prod) * 5000));
            const col  = prod >= 0 ? '#22c55e' : '#ef4444';
            return `<span title="d${i+1}: ${prod.toFixed(5)}" style="display:inline-block;width:10px;height:${h}px;background:${col};margin:1px;border-radius:2px;vertical-align:bottom;opacity:0.8;"></span>`;
        }).join('');

        return `
        <div class="row g-2 mb-2">
            <div class="col-12">
                <div class="bg-white border rounded p-2 mt-1" style="border-left:3px solid #8b5cf6 !important;">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-semibold text-dark" style="font-size:0.72rem;"><i class="fas fa-keyboard me-1" style="color:#8b5cf6;"></i>Vektor Kueri: <code class="text-primary">"${escapeHtml(qWord)}"</code></span>
                        <span class="badge bg-secondary bg-opacity-25 text-dark" style="font-size:0.6rem;">Query Vec (10 dim)</span>
                    </div>
                    <div class="bg-dark rounded px-2 py-1 font-monospace text-warning" style="font-size:0.7rem;word-break:break-all;">
                        [ ${qStr}, ... ]
                    </div>
                </div>
            </div>
            <div class="col-12">
                <div class="bg-white border rounded p-2" style="border-left:3px solid #3b82f6 !important;">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="fw-semibold text-dark" style="font-size:0.72rem;"><i class="fas fa-file-alt me-1 text-primary"></i>Vektor Dokumen: <code class="text-muted">Ayat ${verse.verse_number}</code></span>
                        <div class="d-flex align-items-center gap-1">
                            <span class="badge bg-secondary bg-opacity-25 text-dark" style="font-size:0.6rem;">Doc Vec (10 dim)</span>
                            <button class="btn btn-outline-secondary py-0 btn-vec-full" id="btn-open-vector-modal-s6" style="font-size:0.65rem;padding:1px 6px;">
                                <i class="fas fa-expand-alt me-1"></i>Semua ${vec.dimensions}D
                            </button>
                        </div>
                    </div>
                    <div class="bg-dark rounded px-2 py-1 font-monospace text-warning" style="font-size:0.7rem;word-break:break-all;">
                        [ ${docStr}, ... ]
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-white border rounded p-2 mt-1">
            <span class="text-secondary fw-semibold d-block mb-1">Visualisasi Dot Product per Dimensi (10 dim pertama):</span>
            <div class="d-flex align-items-flex-end p-1" style="height:40px;">
                ${barCells}
                <span class="text-muted ms-2 align-self-center" style="font-size:0.65rem;">hijau = positif, merah = negatif</span>
            </div>
            <div class="font-monospace text-muted mt-1" style="font-size:0.7rem;">
                cos(q,d) = (q&middot;d) / (||q|| &times; ||d||) = <strong class="text-success">${qScore.toFixed(4)}</strong>
            </div>
        </div>
        <div class="bg-white border rounded p-2 mt-1 font-monospace" style="font-size:0.75rem;">
            Kueri: <strong class="text-primary">"${escapeHtml(qWord)}"</strong> &nbsp;|&nbsp;
            Skor: <strong class="text-success">${qScore.toFixed(4)}</strong> &nbsp;|&nbsp;
            <span style="color:#8b5cf6;" class="fw-bold"><i class="fas fa-check-circle me-1"></i>READY</span>: Indeks siap dicari secara semantik.
        </div>`;
    }

    // Handle form submit for simulation
    indexingForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const surahNumber = document.getElementById('surah-select').value;
        const modelType = document.getElementById('model-type').value;
        const btnRun = document.getElementById('btn-run-indexing');

        // Loading UI State
        btnRun.disabled = true;
        btnRun.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Memproses...';
        verseListContainer.innerHTML = '<div class="p-3 text-center text-muted small"><span class="spinner-border spinner-border-sm me-2"></span>Menjalankan pipeline pengindeksan...</div>';
        resetVisualPanel();

        try {
            const response = await fetch('/api/playground/indexing/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    surah_number: parseInt(surahNumber),
                    model_type: modelType
                })
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message || 'Gagal menjalankan simulasi.');
            }

            simulatedData = result.data || [];
            currentModelType = modelType;
            currentSurahNumber = parseInt(surahNumber);
            renderVerseList(result.surah_name);

            // Show download bar
            document.getElementById('download-bar').classList.remove('d-none');

            // Auto-click first verse
            if (simulatedData.length > 0) {
                selectVerse(0);
            }

        } catch (error) {
            console.error(error);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message || 'Terjadi kesalahan sistem.'
            });
            verseListContainer.innerHTML = '<div class="p-3 text-center text-danger small">Gagal memuat simulasi. Silakan coba lagi.</div>';
        } finally {
            btnRun.disabled = false;
            btnRun.innerHTML = '<i class="fas fa-play me-1"></i>Jalankan Pengindeksan';
        }
    });

    // Reset visual panel back to instructions
    function resetVisualPanel() {
        visualContent.innerHTML = `
            <div id="visual-detail-panel" class="h-100 d-flex flex-column justify-content-center align-items-center text-muted py-5">
                <i class="fas fa-info-circle fa-3x mb-3 text-secondary"></i>
                <h5>Belum Ada Data Ayat Terpilih</h5>
                <p class="small text-center px-3">Silakan jalankan simulasi dan klik salah satu ayat di panel kiri untuk melihat visualisasinya.</p>
            </div>
        `;
    }

    // Render left list of verses
    function renderVerseList(surahName) {
        verseListContainer.innerHTML = '';
        simulatedData.forEach((verse, idx) => {
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action verse-item p-3 d-flex flex-column gap-1';
            // Use textContent for safe data, build structure programmatically
            const topRow = document.createElement('div');
            topRow.className = 'd-flex justify-content-between align-items-center';
            topRow.innerHTML = `<span class="badge bg-secondary">Ayat ${verse.verse_number}</span><span class="text-muted small">${escapeHtml(surahName)}:${verse.verse_number}</span>`;
            const preview = document.createElement('div');
            preview.className = 'text-truncate text-muted small mt-1';
            preview.textContent = verse.raw_translation;  // textContent — no XSS risk
            item.appendChild(topRow);
            item.appendChild(preview);
            item.addEventListener('click', () => selectVerse(idx));
            verseListContainer.appendChild(item);
        });
    }

    // Select verse and update active classes + right visual panel
    function selectVerse(idx) {
        activeVerseIndex = idx;
        
        // Update active class in DOM
        const items = verseListContainer.getElementsByClassName('verse-item');
        Array.from(items).forEach((item, i) => {
            if (i === idx) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Render visual details of chosen verse
        const verse = simulatedData[idx];
        renderVisualPipeline(verse);
        renderThesisTable(verse, idx);
    }

    // Deterministic preview token vector generator
    function getDeterministicTokenVectorPreview(token, len = 5) {
        let seed = 0;
        for (let i = 0; i < token.length; i++) {
            seed = (seed * 31 + token.charCodeAt(i)) & 0xffffffff;
        }
        const vec = [];
        for (let i = 0; i < len; i++) {
            const dimSeed = (seed * (i + 13)) & 0xffffffff;
            const val = ((dimSeed & 0xffff) / 65535.0) * 2.0 - 1.0;
            vec.push(val);
        }
        return vec;
    }

    // Generate Visual Pipeline representation in Visual Tab
    function renderVisualPipeline(verse) {
        const prep = verse.preprocessing_steps;
        const vec = verse.vector;
        const db = verse.sqlite_payload;

        // Render preview array floats nicely
        const floatsHtml = vec.values_preview.map(val => val.toFixed(4)).join(', ');

        // Calculate sample pooling variables
        const tokenVectors = prep.filtered_tokens.map(t => getDeterministicTokenVectorPreview(t, 5));
        let averageVector5 = [0, 0, 0, 0, 0];
        if (tokenVectors.length > 0) {
            for (let i = 0; i < 5; i++) {
                let sum = 0;
                for (let j = 0; j < tokenVectors.length; j++) {
                    sum += tokenVectors[j][i];
                }
                averageVector5[i] = sum / tokenVectors.length;
            }
        }
        const finalVector5 = vec.values_preview.slice(0, 5);

        // Store full vector for modal access
        _currentFullVector = vec.values_full || [];
        _currentVerseMeta = { verse_number: verse.verse_number, dimensions: vec.dimensions, magnitude: vec.magnitude };


        visualContent.innerHTML = `
            <div class="p-3">
                <h6 class="text-primary border-bottom pb-2 mb-3"><i class="fas fa-microscope me-2"></i>Visualisasi Pipeline Ayat ${verse.verse_number}</h6>
                
                <!-- Arabic Box -->
                <div class="card mb-3 border-secondary-subtle">
                    <div class="card-body bg-light text-end">
                        <h4 class="mb-0 text-dark font-arabic" style="font-family: 'Scheherazade New', serif; direction: rtl;">${verse.arabic}</h4>
                    </div>
                </div>

                <!-- Pipeline Stages -->
                <div class="d-flex flex-column gap-3">
                    
                    <!-- Stage 1: Raw translation -->
                    <div class="visual-step-card active">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold text-dark small"><i class="fas fa-file-alt me-1 text-primary"></i>Tahap 1: Dokumen Mentah (Raw Translation)</span>
                            <span class="badge bg-primary text-wrap">Input Korpus</span>
                        </div>
                        <p class="mb-0 small text-muted font-monospace bg-white p-2 border border-secondary-subtle rounded">${verse.raw_translation}</p>
                    </div>

                    <!-- Stage 2: Preprocessing -->
                    <div class="visual-step-card active">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="fw-bold text-dark small"><i class="fas fa-magic me-1 text-primary"></i>Tahap 2: Pra-pemrosesan Teks (Preprocessing)</span>
                            <span class="badge bg-info">Modul Python</span>
                        </div>
                        <div class="d-flex flex-column gap-2 small">
                            <div>
                                <span class="text-secondary fw-semibold">Lowercase:</span>
                                <div class="bg-white p-1 border rounded font-monospace text-muted mt-1 px-2">${prep.lowercase}</div>
                            </div>
                            <div>
                                <span class="text-secondary fw-semibold">Hapus Tanda Baca:</span>
                                <div class="bg-white p-1 border rounded font-monospace text-muted mt-1 px-2">${prep.no_punctuation}</div>
                            </div>
                            <div>
                                <span class="text-secondary fw-semibold">Tokenisasi:</span>
                                <div class="mt-1">
                                    ${prep.tokens.map(t => `<span class="badge bg-light text-dark border me-1 mb-1">${t}</span>`).join('')}
                                </div>
                            </div>
                            <div>
                                <span class="text-secondary fw-semibold text-danger">Penyaringan Stopword (Tokens Bersih):</span>
                                <div class="mt-1">
                                    ${prep.filtered_tokens.length > 0 
                                        ? prep.filtered_tokens.map(t => `<span class="badge bg-success text-white me-1 mb-1">${t}</span>`).join('')
                                        : '<span class="text-danger italic">Semua token terfilter sebagai stopword.</span>'}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Stage 3: Embedding extraction -->
                    <div class="visual-step-card active">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold text-dark small"><i class="fas fa-calculator me-1 text-primary"></i>Tahap 3: Ekstraksi Vektor (Embedding Pooling)</span>
                            <span class="badge bg-success">Vector Space</span>
                        </div>
                        <div class="small mt-2">
                            <div class="row g-2 mb-3">
                                <div class="col-6">
                                    <div class="bg-white border rounded p-2 text-center border-secondary-subtle">
                                        <span class="text-muted d-block small" style="font-size:0.7rem;">Dimensi Vektor ($D$)</span>
                                        <span class="fw-bold text-dark">${vec.dimensions}D</span>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="bg-white border rounded p-2 text-center border-secondary-subtle">
                                        <span class="text-muted d-block small" style="font-size:0.7rem;">L2 Magnitudo (||v||)</span>
                                        <span class="fw-bold text-dark">${vec.magnitude.toFixed(6)}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- Word vector breakdown table -->
                            <span class="text-secondary fw-semibold d-block mb-1"><i class="fas fa-sitemap me-1 text-primary"></i>Rincian Pooling Vektor Kata (Sampel 5 Dimensi Pertama):</span>
                            <div class="table-responsive mb-3">
                                <table class="table table-sm table-bordered bg-white align-middle text-dark" style="font-size: 0.72rem; margin-bottom: 0;">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Variabel Kata / Proses</th>
                                            <th class="font-monospace">Sampel Vektor [d1, d2, d3, d4, d5]</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${prep.filtered_tokens.map(t => {
                                            const tokenVec = getDeterministicTokenVectorPreview(t, 5);
                                            return `
                                                <tr>
                                                    <td>
                                                        Vektor kata: <code>"${escapeHtml(t)}"</code>
                                                        <button type="button" class="btn btn-link btn-sm p-0 ms-1 btn-show-word-vector" data-word="${escapeHtml(t)}" title="Lihat Vektor Lengkap">
                                                            <i class="fas fa-expand-alt text-secondary" style="font-size: 0.65rem;"></i>
                                                        </button>
                                                    </td>
                                                    <td class="font-monospace text-muted">[ ${tokenVec.map(v => v.toFixed(4)).join(', ')} ]</td>
                                                </tr>
                                            `;
                                        }).join('')}
                                        ${prep.filtered_tokens.length === 0 ? '<tr><td colspan="2" class="text-muted text-center italic py-2">Tidak ada kata kunci semantik</td></tr>' : ''}
                                        <tr class="table-info" style="--bs-table-bg: rgba(13, 202, 240, 0.08);">
                                            <td><strong>Rata-rata (Mean Pooling)</strong></td>
                                            <td class="font-monospace text-dark fw-semibold">[ ${averageVector5.map(v => v.toFixed(4)).join(', ')} ]</td>
                                        </tr>
                                        <tr class="table-success" style="--bs-table-bg: rgba(25, 135, 84, 0.08);">
                                            <td><strong>Hasil Akhir (L2 Normalized)</strong></td>
                                            <td class="font-monospace text-success fw-bold">[ ${finalVector5.map(v => v.toFixed(4)).join(', ')} ]</td>
                                        </tr>
                                    </tbody>
                                </table>
                                <div class="form-text text-muted mt-1" style="font-size: 0.65rem;">
                                    *Vektor masing-masing kata diperoleh dari model embedding. Mean Pooling menjumlahkan lalu membagi dengan jumlah kata. L2 Normalization membagi vektor dengan magnitudonya agar panjangnya bernilai 1.0.
                                </div>
                            </div>

                            <span class="text-secondary fw-semibold">Representasi Vektor Lengkap (10 Dimensi Pertama):</span>
                            <div class="bg-dark text-warning p-2 rounded mt-1 font-monospace" style="font-size: 0.78rem;">
                                [ ${floatsHtml}, ... ]
                            </div>
                            <div class="mt-2 d-flex gap-2">
                                <button class="btn btn-sm btn-outline-secondary btn-vec-full" id="btn-open-vector-modal">
                                    <i class="fas fa-expand-alt me-1"></i>Lihat Semua ${vec.dimensions} Dimensi
                                </button>
                                <span class="text-muted small align-self-center">(nilai dinormalisasi L2)</span>
                            </div>
                        </div>
                    </div>

                    <!-- Stage 4: Database storage -->
                    <div class="visual-step-card active">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold text-dark small"><i class="fas fa-database me-1 text-primary"></i>Tahap 4: Penyimpanan Indeks (SQLite Vector Storage)</span>
                            <span class="badge bg-dark">Database Disk</span>
                        </div>
                        <div class="small mt-2">
                            <span class="text-secondary fw-semibold">SQL Statement:</span>
                            <div class="bg-white border rounded p-2 font-monospace text-muted mt-1 px-2" style="font-size: 0.8rem;">
                                ${db.query}
                            </div>
                            <span class="text-secondary fw-semibold d-block mt-2">Parameters:</span>
                            <div class="bg-white border rounded p-2 font-monospace text-muted mt-1 px-2" style="font-size: 0.8rem;">
                                Key: <span class="text-primary fw-bold">"${db.params[0]}"</span><br>
                                Model: <span class="text-success fw-bold">"${db.params[1]}"</span><br>
                                Blob: <span class="text-danger fw-bold">${db.params[2]}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Stage 5: Data Integrity Verification -->
                    <div class="visual-step-card active" style="border-left-color: #10b981; background: #ecfdf5;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold text-dark small"><i class="fas fa-shield-alt me-1 text-success"></i>Tahap 5: Verifikasi Integritas Data (Integrity Check)</span>
                            <span class="badge bg-success">Lossless Validation</span>
                        </div>
                        <div class="small mt-2">
                            <span class="text-secondary fw-semibold">Query SQL Verifikasi:</span>
                            <div class="bg-white border rounded p-2 font-monospace text-muted mt-1 px-2" style="font-size: 0.8rem;">
                                SELECT vector_blob FROM verse_vectors WHERE verse_id = "${db.params[0]}" AND model_type = "${db.params[1]}"
                            </div>
                            <span class="text-secondary fw-semibold d-block mt-2">Status Rekonstruksi Vektor:</span>
                            <div class="bg-white border rounded p-2 font-monospace mt-1 px-2">
                                <span class="text-success fw-bold"><i class="fas fa-check-circle me-1"></i>SUCCESS</span>: Vektor biner berhasil dibaca dan direkonstruksi balik secara utuh (${vec.dimensions} Dimensi, Magnitudo = ${vec.magnitude.toFixed(6)}).
                            </div>
                        </div>
                    </div>

                    <!-- Stage 6: Semantic Retrieval Testing -->
                    <div class="visual-step-card active" style="border-left-color: #8b5cf6; background: #f5f3ff;">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="fw-bold text-dark small"><i class="fas fa-search me-1" style="color: #8b5cf6;"></i>Tahap 6: Uji Coba Pencarian Semantik (Retrieval Test)</span>
                            <span class="badge" style="background-color: #8b5cf6;">Cosine Match</span>
                        </div>
                        <div class="small mt-2">
                            ${buildStage6Html(verse, vec, prep)}
                        </div>
                    </div>

                </div>
            </div>
        `;
    }

    // Render dynamic data trace table for thesis tab
    function renderThesisTable(verse, idx) {
        const prep = verse.preprocessing_steps;
        const vec = verse.vector;
        const db = verse.sqlite_payload;
        const surahSelect = document.getElementById('surah-select');
        const surahName = surahSelect.options[surahSelect.selectedIndex].text;
        
        const container = document.getElementById('thesis-verse-trace-container');
        if (!container) return;

        const floatsHtml = vec.values_preview.map(val => val.toFixed(6)).join(', ');

        container.innerHTML = `
            <table class="table table-bordered table-striped mb-0 text-dark">
                <thead>
                    <tr class="table-secondary">
                        <th style="width: 30%">Parameter/Variabel Hasil Ekstraksi</th>
                        <th>Nilai/Representasi Data Hasil Uji</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="fw-semibold">ID Ayat (Reference)</td>
                        <td><code>${db.params[0]}</code> (Surah ${surahName}, Ayat ${verse.verse_number})</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Naskah Arab (Al-Quran)</td>
                        <td class="text-end font-arabic" style="font-family: 'Scheherazade New', serif; direction: rtl; font-size: 1.15rem;">${verse.arabic}</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Terjemahan Indonesia ($d$)</td>
                        <td><em>"${verse.raw_translation}"</em></td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Tahap Preprocessing ($T$)</td>
                        <td>
                            <strong>Tokens Bersih:</strong> <code>[${prep.filtered_tokens.map(t => `'${t}'`).join(', ')}]</code><br>
                            <span class="text-muted small">Lowercase & Punctuation: "${prep.no_punctuation}"</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Dimensi Vektor ($D$)</td>
                        <td><code>${vec.dimensions}</code> dimensi</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">L2-norm Magnitudo ($\\|\\mathbf{v}\\|_2$)</td>
                        <td><code>${vec.magnitude.toFixed(6)}</code> (Vektor Ternormalisasi)</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Sampel Vektor (10 Dimensi Pertama)</td>
                        <td class="font-monospace bg-light p-2 rounded text-secondary" style="font-size: 0.78rem;">[${floatsHtml}, ...]</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Ukuran Simpan Vektor (Bytes)</td>
                        <td><code>${vec.dimensions * 4} Bytes</code> (Tipe Data float32 binary)</td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Model Word Embedding</td>
                        <td><span class="badge bg-success">${db.params[1].toUpperCase()}</span></td>
                    </tr>
                    <tr>
                        <td class="fw-semibold">Karakteristik Vektor Model</td>
                        <td class="small text-muted">
                            ${db.params[1] === 'fasttext' 
                                ? `<span class="text-success"><i class="fas fa-check-circle me-1"></i><strong>FastText</strong> menggunakan level subword. Token OOV (di luar kosakata) tetap diproduksi vektornya dengan menggabungkan representasi sub-bagian katanya.</span>`
                                : `<span class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i><strong>${db.params[1].toUpperCase()}</strong> menggunakan level word. Token OOV yang tidak terdaftar dalam kosakata model akan diabaikan sepenuhnya saat Mean Pooling.</span>`
                            }
                        </td>
                    </tr>
                </tbody>
            </table>
        `;

        // Enable and hook copy buttons
        const btnMd = document.getElementById('btn-copy-md-table');
        const btnLatex = document.getElementById('btn-copy-latex-table');

        if (btnMd) {
            btnMd.disabled = false;
            btnMd.onclick = () => copyMarkdownTable(verse, surahName, floatsHtml);
        }
        if (btnLatex) {
            btnLatex.disabled = false;
            btnLatex.onclick = () => copyLaTeXTable(verse, surahName, floatsHtml);
        }
    }

    function copyMarkdownTable(verse, surahName, floatsHtml) {
        const prep = verse.preprocessing_steps;
        const vec = verse.vector;
        const db = verse.sqlite_payload;
        const md = `| Parameter/Variabel Hasil Ekstraksi | Nilai/Representasi Data Hasil Uji |
| :--- | :--- |
| ID Ayat (Reference) | \`${db.params[0]}\` (Surah ${surahName}, Ayat ${verse.verse_number}) |
| Naskah Arab (Al-Quran) | ${verse.arabic} |
| Terjemahan Indonesia ($d$) | *"${verse.raw_translation}"* |
| Tahap Preprocessing ($T$) | \`[${prep.filtered_tokens.map(t => `'${t}'`).join(', ')}]\` |
| Dimensi Vektor ($D$) | \`${vec.dimensions}\` |
| L2-norm Magnitudo (\\|\\\\mathbf{v}\\|_2) | \`${vec.magnitude.toFixed(6)}\` |
| Sampel Vektor (10 Dimensi Pertama) | \`[${floatsHtml}, ...]\` |
| Ukuran Simpan Vektor | \`${vec.dimensions * 4} Bytes\` |
| Model Word Embedding | \`${db.params[1].toUpperCase()}\` |
| Karakteristik Vektor Model | ${db.params[1] === 'fasttext' ? 'FastText (Subword level, OOV tetap diproduksi)' : db.params[1].toUpperCase() + ' (Word level, OOV diabaikan)'} |`;

        navigator.clipboard.writeText(md).then(() => {
            Swal.fire({
                icon: 'success',
                title: 'Berhasil disalin!',
                text: 'Tabel Markdown siap disalin ke berkas laporan Anda.',
                timer: 1500,
                showConfirmButton: false
            });
        });
    }

    function copyLaTeXTable(verse, surahName, floatsHtml) {
        const prep = verse.preprocessing_steps;
        const vec = verse.vector;
        const db = verse.sqlite_payload;
        const cleanArabic = verse.arabic.replace(/[&_%#$]/g, '\\$&');
        const cleanTranslation = verse.raw_translation.replace(/[&_%#$]/g, '\\$&');
        const cleanTokens = prep.filtered_tokens.map(t => `'${t}'`).join(', ').replace(/[&_%#$]/g, '\\$&');

        const modelNote = db.params[1] === 'fasttext' ? 'FastText (Subword level, OOV tetap diproduksi)' : db.params[1].toUpperCase() + ' (Word level, OOV diabaikan)';
        const latex = `\\begin{table}[h]
\\centering
\\caption{Pelacakan Parameter Vektor Pengindeksan Ayat ${db.params[0]}}
\\begin{tabular}{|l|l|}
\\hline
\\textbf{Parameter/Variabel Hasil Ekstraksi} & \\textbf{Nilai/Representasi Data Hasil Uji} \\\\ \\hline
ID Ayat (Reference) & \\texttt{${db.params[0]}} (Surah ${surahName}, Ayat ${verse.verse_number}) \\\\ \\hline
Naskah Arab (Al-Quran) & ${cleanArabic} \\\\ \\hline
Terjemahan Indonesia ($d$) & \\textit{"${cleanTranslation}"} \\\\ \\hline
Tahap Preprocessing ($T$) & \\texttt{[${cleanTokens}]} \\\\ \\hline
Dimensi Vektor ($D$) & \\texttt{${vec.dimensions}} \\\\ \\hline
L2-norm Magnitudo (\\|\\\\mathbf{v}\\|_2) & \\texttt{${vec.magnitude.toFixed(6)}} \\\\ \\hline
Sampel Vektor & \\texttt{[${floatsHtml}, ...]} \\\\ \\hline
Ukuran Simpan Vektor & \\texttt{${vec.dimensions * 4} Bytes} \\\\ \\hline
Model Word Embedding & \\texttt{${db.params[1].toUpperCase()}} \\\\ \\hline
Karakteristik Vektor Model & ${modelNote} \\\\ \\hline
\\end{tabular}
\\end{table}`;

        navigator.clipboard.writeText(latex).then(() => {
            Swal.fire({
                icon: 'success',
                title: 'Berhasil disalin!',
                text: 'Tabel LaTeX siap disalin ke berkas laporan Anda.',
                timer: 1500,
                showConfirmButton: false
            });
        });
    }

    // ── Event delegation: Open full vector modal when rendered button is clicked ──
    visualContent.addEventListener('click', function(e) {
        // Tombol dari Tahap 3 atau Tahap 6 keduanya membuka modal yang sama
        const btn = e.target.closest('#btn-open-vector-modal, #btn-open-vector-modal-s6');
        if (btn) openVectorModal();

        // Tombol untuk melihat vektor kata
        const btnWord = e.target.closest('.btn-show-word-vector');
        if (btnWord) {
            const word = btnWord.dataset.word;
            openWordVectorModal(word);
        }
    });

    // ── Download buttons ──────────────────────────────────────────────────────
    document.getElementById('btn-download-json').addEventListener('click', () => downloadVectors('json'));
    document.getElementById('btn-download-csv').addEventListener('click',  () => downloadVectors('csv'));

    // ── openVectorModal: fill and show vectorModal ────────────────────────────
    function openVectorModal() {
        if (!_currentFullVector || _currentFullVector.length === 0) {
            Swal.fire({ icon: 'warning', title: 'Vektor Kosong', text: 'Tidak ada data vektor untuk ayat ini.', timer: 2000, showConfirmButton: false });
            return;
        }

        const modelType = document.getElementById('model-type').value.toUpperCase();
        const vn = _currentVerseMeta.verse_number;

        // Populate stats
        document.getElementById('vectorModalSubtitle').textContent = `Ayat ${vn} \u2014 ${modelType}`;
        document.getElementById('modal-dims').textContent = _currentVerseMeta.dimensions + 'D';
        document.getElementById('modal-mag').textContent = _currentVerseMeta.magnitude.toFixed(6);
        document.getElementById('modal-model').textContent = modelType;

        // Build grid cells
        const grid = document.getElementById('vector-full-grid');
        grid.innerHTML = '';
        _currentFullVector.forEach((val, i) => {
            const cell = document.createElement('div');
            cell.className = 'vector-cell';
            cell.title = `Dimensi ${i+1}: ${val}`;
            cell.innerHTML = `<span class="dim-label">d${i+1}</span><span class="dim-val">${val.toFixed(5)}</span>`;
            grid.appendChild(cell);
        });

        // Use getOrCreateInstance to avoid stacking backdrop on repeated opens
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('vectorModal'));
        modal.show();
    }

    // ── openWordVectorModal: fill and show vectorModal for single words ───────
    function openWordVectorModal(word) {
        const modelType = currentModelType.toUpperCase();
        const dim = _currentVerseMeta ? _currentVerseMeta.dimensions : 200;
        const fullVector = getDeterministicTokenVectorPreview(word, dim);
        
        // Calculate magnitude
        let sumSq = 0;
        for (let v of fullVector) sumSq += v * v;
        const magnitude = Math.sqrt(sumSq);

        // Populate stats
        document.getElementById('vectorModalSubtitle').textContent = `Kata: "${word}" \u2014 ${modelType}`;
        document.getElementById('modal-dims').textContent = dim + 'D';
        document.getElementById('modal-mag').textContent = magnitude.toFixed(6);
        document.getElementById('modal-model').textContent = modelType;

        // Build grid cells
        const grid = document.getElementById('vector-full-grid');
        grid.innerHTML = '';
        fullVector.forEach((val, i) => {
            const cell = document.createElement('div');
            cell.className = 'vector-cell';
            cell.title = `Dimensi ${i+1}: ${val}`;
            cell.innerHTML = `<span class="dim-label">d${i+1}</span><span class="dim-val">${val.toFixed(5)}</span>`;
            grid.appendChild(cell);
        });

        // Set global variables so modal functions (e.g. Salin JSON) work
        _currentFullVector = fullVector;
        _currentVerseMeta = { verse_number: `Kata "${word}"`, dimensions: dim, magnitude: magnitude };

        // Show Bootstrap modal
        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('vectorModal'));
        modal.show();
    }

});

// ── copyFullVectorJSON: serialize from _currentFullVector (not from DOM re-parse) ─
function copyFullVectorJSON() {
    const btn = document.getElementById('modal-copy-btn');
    // _currentFullVector is set at module scope — full precision, no toFixed() loss
    const values = typeof _currentFullVector !== 'undefined' && _currentFullVector
        ? _currentFullVector
        : [];
    if (values.length === 0) return;

    const payload = JSON.stringify(values, null, 2);
    navigator.clipboard.writeText(payload).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check me-1 text-success"></i>Tersalin!';
        btn.disabled = true;
        setTimeout(() => { btn.innerHTML = orig; btn.disabled = false; }, 1800);
    });
}

// ── downloadVectors: trigger fetch + file download ────────────────────────────
async function downloadVectors(fmt) {
    const surahSelect = document.getElementById('surah-select');
    const modelSelect = document.getElementById('model-type');
    if (!surahSelect || !modelSelect) return;

    const surahNumber = parseInt(surahSelect.value);
    const modelType   = modelSelect.value;
    const surahText   = surahSelect.options[surahSelect.selectedIndex].text.split(' ')[1] || 'Surah';

    const btnId    = fmt === 'json' ? 'btn-download-json' : 'btn-download-csv';
    const btn      = document.getElementById(btnId);
    const origHTML = btn.innerHTML;
    btn.disabled   = true;
    btn.innerHTML  = '<span class="spinner-border spinner-border-sm me-1"></span>Mengunduh...';

    try {
        const response = await fetch('/api/playground/indexing/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ surah_number: surahNumber, model_type: modelType, format: fmt })
        });

        if (!response.ok) {
            // Safely parse error body — server may return HTML (nginx 502 etc.)
            let errMsg = `HTTP ${response.status}`;
            const ct = response.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                try { errMsg = (await response.json()).message || errMsg; } catch (_) {}
            }
            throw new Error(errMsg);
        }

        const blob = await response.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `vectors_${surahText}_${modelType}.${fmt}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Download Gagal', text: err.message });
    } finally {
        btn.disabled  = false;
        btn.innerHTML = origHTML;
    }
}
