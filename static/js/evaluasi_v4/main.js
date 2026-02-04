/**
 * Main Module for Integrated Evaluation
 * Orchestrates the application logic and event handling
 */
import { api } from './api.js';
import { ui } from './ui.js';
import { CRUDManager } from './crud.js';

document.addEventListener("DOMContentLoaded", function () {
    // DOM Elements
    const evaluasiResult = document.getElementById("evaluasi-result");
    const formEvaluasi = document.getElementById("form-evaluasi");
    const inputQueryText = document.getElementById("input-query-text");
    const toggleAdvancedSettings = document.getElementById("toggle-advanced-settings");
    const advancedSettings = document.getElementById("advanced-settings");
    const ensembleMethod = document.getElementById("ensemble-method");

    const useFinalThreshold = document.getElementById("use-final-threshold");
    const finalThresholdWrapper = document.getElementById("final-threshold-wrapper");
    const ensembleThresholdInput = document.getElementById("ensemble-threshold");

    // Per-model Threshold Sliders
    const w2vThreshold = document.getElementById("w2v-threshold");
    const ftThreshold = document.getElementById("ft-threshold");
    const gloveThreshold = document.getElementById("glove-threshold");
    const w2vThresholdVal = document.getElementById("w2v-threshold-val");
    const ftThresholdVal = document.getElementById("ft-threshold-val");
    const gloveThresholdVal = document.getElementById("glove-threshold-val");
    const w2vImpact = document.getElementById("w2v-impact");
    const ftImpact = document.getElementById("ft-impact");
    const gloveImpact = document.getElementById("glove-impact");

    const votingBonus = document.getElementById("voting-bonus");
    const useVotingFilter = document.getElementById("use-voting-filter");

    let currentEvaluationResults = null;
    let isEvaluating = false;

    // Final Threshold Toggle
    if (useFinalThreshold) {
        useFinalThreshold.addEventListener("change", function () {
            finalThresholdWrapper.classList.toggle("d-none", !this.checked);
        });
    }

    // Initialize CRUD Manager
    const crud = new CRUDManager({
        onQuerySelected: (query) => {
            if (query) {
                inputQueryText.value = query.text;
                formEvaluasi.classList.remove("d-none");
            } else {
                formEvaluasi.classList.add("d-none");
            }
            evaluasiResult.innerHTML = "";
        }
    });

    crud.loadQueries();

    // Event Listeners for Threshold Sliders
    w2vThreshold.addEventListener("input", () => ui.updateThresholdDisplay(w2vThreshold, w2vThresholdVal, w2vImpact));
    ftThreshold.addEventListener("input", () => ui.updateThresholdDisplay(ftThreshold, ftThresholdVal, ftImpact));
    gloveThreshold.addEventListener("input", () => ui.updateThresholdDisplay(gloveThreshold, gloveThresholdVal, gloveImpact));

    // Toggle Advanced Settings
    toggleAdvancedSettings.addEventListener("click", function () {
        const isHidden = advancedSettings.style.display === "none";
        advancedSettings.style.display = isHidden ? "block" : "none";
        this.innerHTML = isHidden ?
            '<i class="fas fa-cog me-1"></i>Sembunyikan Pengaturan' :
            '<i class="fas fa-cog me-1"></i>Pengaturan Lanjutan';
    });

    // Select All Methods
    document.querySelectorAll(".select-all-methods").forEach((btn) => {
        btn.addEventListener("click", function () {
            const checkboxes = document.querySelectorAll(".eval-method");
            const allChecked = Array.from(checkboxes).every((cb) => cb.checked);
            checkboxes.forEach((cb) => (cb.checked = !allChecked));
        });
    });

    // Run Evaluation
    formEvaluasi.addEventListener("submit", async function (e) {
        e.preventDefault();
        if (isEvaluating || !crud.selectedQueryId) return;

        const payload = {
            query_text: inputQueryText.value.trim(),
            result_limit: parseInt(document.getElementById("result-limit").value),
            selected_methods: Array.from(document.querySelectorAll(".eval-method:checked")).map(cb => cb.value),
            ensemble_config: {
                method: ensembleMethod.value,
                w2v_threshold: parseFloat(w2vThreshold.value),
                ft_threshold: parseFloat(ftThreshold.value),
                glove_threshold: parseFloat(gloveThreshold.value),
                voting_bonus: parseFloat(votingBonus.value),
                use_voting_filter: useVotingFilter.checked,
            },
            threshold_per_model: {
                // If switch is off, send 0 to return all results that pass base models
                ensemble: useFinalThreshold.checked ? parseFloat(ensembleThresholdInput.value) : 0,
                word2vec: parseFloat(w2vThreshold.value),
                fasttext: parseFloat(ftThreshold.value),
                glove: parseFloat(gloveThreshold.value),
            }
        };

        if (payload.selected_methods.length === 0) {
            Swal.fire("Error", "Pilih minimal satu metode", "error");
            return;
        }

        ui.showSpinner(evaluasiResult, "Mengevaluasi...");
        isEvaluating = true;
        const runBtn = formEvaluasi.querySelector('button[type="submit"]');
        runBtn.disabled = true;

        try {
            const data = await api.runEvaluation(crud.selectedQueryId, payload);
            if (data.success) {
                currentEvaluationResults = data;
                renderResults(data);
                Swal.fire({ icon: 'success', title: 'Selesai', timer: 1000, showConfirmButton: false });
            } else {
                evaluasiResult.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
        } catch (err) {
            evaluasiResult.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
        } finally {
            isEvaluating = false;
            runBtn.disabled = false;
        }
    });

    function renderResults(data) {
        const results = data.results;
        const ensembleAnalysis = data.ensemble_analysis;

        let html = '<div class="table-responsive shadow-sm rounded overflow-hidden"><table class="table table-sm table-hover align-middle small mb-0">';
        html += '<thead class="table-dark"><tr><th>Metode</th><th>Threshold</th><th>Prec.</th><th>Recall</th><th>F1</th><th>Acc.</th><th>TP</th><th>FP</th><th>FN</th></tr></thead><tbody>';

        results.forEach((r) => {
            if (r.error) {
                html += `<tr><td colspan="10" class="text-danger">${r.label}: ${r.error}</td></tr>`;
            } else {
                const isWinner = ensembleAnalysis && (r.method.startsWith('ensemble') && r.f1 === ensembleAnalysis.best_f1[1].f1);
                html += `<tr ${isWinner ? 'class="table-success"' : ""}>`;
                html += `<td><strong>${r.label}</strong> ${isWinner ? '★' : ''}</td>`;
                html += `<td><span class="badge bg-light text-dark border">${r.threshold !== null ? r.threshold.toFixed(2) : '-'}</span></td>`;
                html += `<td>${ui.formatPercent(r.precision)}</td>`;
                html += `<td>${ui.formatPercent(r.recall)}</td>`;
                html += `<td><strong>${ui.formatPercent(r.f1)}</strong></td>`;
                html += `<td>${ui.formatPercent(r.accuracy)}</td>`;
                html += `<td>${r.tp_verses ? r.tp_verses.length : (r.true_positive || 0)}</td>`;
                html += `<td>${r.fp_verses ? r.fp_verses.length : (r.false_positive || 0)}</td>`;
                html += `<td>${r.fn_verses ? r.fn_verses.length : (r.false_negative || 0)}</td>`;
                html += "</tr>";
            }
        });
        html += "</tbody></table></div>";
        evaluasiResult.innerHTML = html;
        // Add Listeners
        evaluasiResult.querySelectorAll(".btn-show-detail").forEach(btn => {
            btn.addEventListener("click", () => {
                const method = btn.dataset.method;
                const result = results.find(r => r.method === method);
                if (result) showResultDetail(result);
            });
        });
    }

    async function showResultDetail(result) {
        const modal = new bootstrap.Modal(document.getElementById("resultDetailModal"));
        document.getElementById("result-detail-title").textContent = `Analisis Performa: ${result.label}`;
        document.getElementById("detail-tp").textContent = result.true_positive;
        document.getElementById("detail-fp").textContent = result.false_positive;
        document.getElementById("detail-fn").textContent = result.false_negative;

        const f1Percent = (result.f1 * 100).toFixed(1) + '%';
        document.getElementById("detail-f1").textContent = f1Percent;
        document.getElementById("detail-f1-progress").style.width = f1Percent;

        const precPercent = (result.precision * 100).toFixed(1) + '%';
        document.getElementById("detail-precision").textContent = precPercent;
        document.getElementById("detail-precision-progress").style.width = precPercent;

        const recallPercent = (result.recall * 100).toFixed(1) + '%';
        document.getElementById("detail-recall").textContent = recallPercent;
        document.getElementById("detail-recall-progress").style.width = recallPercent;

        const accPercent = (result.accuracy * 100).toFixed(1) + '%';
        document.getElementById("detail-accuracy").textContent = accPercent;
        document.getElementById("detail-accuracy-progress").style.width = accPercent;

        // Show Formula/Params Info in a structured way
        let formulaHtml = `<div class="list-group list-group-flush small">`;
        formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Method Key</span><span class="fw-bold">${result.method}</span></div>`;
        formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Core Threshold</span><span class="badge bg-secondary">${result.threshold !== null ? result.threshold.toFixed(2) : 'N/A'}</span></div>`;

        if (result.additional_info) {
            const info = result.additional_info;
            if (info.ensemble_method) formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Ensemble Type</span><span class="text-primary fw-bold">${info.ensemble_method}</span></div>`;
            if (info.thresholds) {
                formulaHtml += `<div class="list-group-item px-0 py-2">
                    <div class="mb-1 text-muted">Sub-model Thresholds:</div>
                    <div class="d-flex gap-2 flex-wrap">
                        <span class="badge bg-light text-dark border">W2V: ${info.thresholds.word2vec.toFixed(2)}</span>
                        <span class="badge bg-light text-dark border">FT: ${info.thresholds.fasttext.toFixed(2)}</span>
                        <span class="badge bg-light text-dark border">Glove: ${info.thresholds.glove.toFixed(2)}</span>
                    </div>
                </div>`;
            }
            if (info.voting_bonus !== undefined) formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Voting Bonus</span><span class="text-success">+${info.voting_bonus.toFixed(2)}</span></div>`;
            if (info.use_voting_filter !== undefined) formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Consensus Filter</span><span>${info.use_voting_filter ? '<i class="fas fa-check-circle text-success"></i> Active' : '<i class="fas fa-times-circle text-muted"></i> Off'}</span></div>`;
        } else if (result.method === 'lexical') {
            formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Engine</span><span>BM25 + Overlap</span></div>`;
        } else {
            formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Engine</span><span>Cosine Similarity</span></div>`;
        }

        formulaHtml += `<div class="list-group-item px-0 py-2 d-flex justify-content-between"><span>Latency</span><span>${result.exec_time}s</span></div>`;
        formulaHtml += `</div>`;
        document.getElementById("model-formula-info").innerHTML = formulaHtml;

        const tbody = document.getElementById("result-detail-table-body");
        tbody.innerHTML = '';

        const tpHits = result.tp_verses.map(ref => ({ ref, status: 'TP', info: 'Relevan & Teridentifikasi' }));
        const fpHits = result.fp_verses.map(ref => ({ ref, status: 'FP', info: 'Ditemukan tapi tidak relevan' }));
        const fnHits = result.fn_verses.map(ref => ({ ref, status: 'FN', info: 'Relevan tapi tidak ditemukan' }));

        const allHits = [...tpHits, ...fpHits, ...fnHits];
        const displayHits = allHits.slice(0, 10);
        const totalCount = allHits.length;

        document.getElementById("total-results-summary").textContent = `${totalCount} temuan total`;

        let html = '';
        displayHits.forEach(hit => {
            let statusBadge = '';
            if (hit.status === 'TP') statusBadge = '<span class="badge bg-success bg-opacity-10 text-success border border-success-subtle w-100">MATCH (TP)</span>';
            else if (hit.status === 'FP') statusBadge = '<span class="badge bg-danger bg-opacity-10 text-danger border border-danger-subtle w-100">NOISE (FP)</span>';
            else statusBadge = '<span class="badge bg-warning bg-opacity-10 text-warning border border-warning-subtle w-100">MISS (FN)</span>';

            html += `<tr>
                <td class="font-monospace fw-bold">${hit.ref}</td>
                <td>${statusBadge}</td>
                <td class="text-muted small">${hit.info}</td>
            </tr>`;
        });

        if (totalCount > 10) {
            html += `<tr><td colspan="3" class="text-center text-muted py-3 bg-light rounded-bottom">Sisa ${totalCount - 10} hasil lainnya diringkas dalam metrik di atas.</td></tr>`;
        } else if (totalCount === 0) {
            html += `<tr><td colspan="3" class="text-center text-muted py-4">Tidak ada data untuk rincian sampel.</td></tr>`;
        }

        tbody.innerHTML = html;
        modal.show();
    }
});
