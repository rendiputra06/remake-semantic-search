import { api } from '../evaluasi_v4/api.js';
import { ui } from './ui.js';
import { runner } from './batch_runner.js';

/**
 * Evaluation V5 - Main Controller (Glass Command Center)
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Laboratorium V5 (Glass Edition) Initialized');

    // State
    const state = {
        allQueries: [],
        filteredQueries: [],
        selectedQuery: null,
        rows: [],
        isRunning: false,
        searchQuery: '',
        batchResults: []
    };

    // Initialize UI
    ui.init({
        onQuerySelect: async (query) => {
            if (state.isRunning) return;
            state.selectedQuery = query;
            ui.showExperimentArea(query);
            ui.renderQueryList(state.filteredQueries, query.id);

            // Setup batches
            resetBatch();

            // Sync ground truth count
            try {
                const gtRes = await api.getRelevantVerses(query.id);
                if (gtRes.success) ui.updateGroundTruth(gtRes.data.length);
            } catch (e) { console.error(e); }
        },
        onAddRow: () => addRow(),
        onRunBatch: () => runBatch(),
        onResetBatch: () => resetBatch(),
        onSearchQuery: (text) => {
            state.searchQuery = text;
            filterQueries();
        },
        onAddQuery: (text, id) => {
            if (typeof text === 'string') {
                handleSaveQuery(text, id);
            } else {
                // It's likely a click event from the "+" button
                ui.showModal('Tambah Query');
            }
        },
        onEditQuery: (query) => {
            ui.showModal('Edit Query', query.text, query.id);
        },
        onDeleteQuery: (id) => handleDeleteQuery(id),
        onExport: () => exportResults()
    });

    // --- Logic ---

    async function loadData() {
        try {
            const res = await api.getQueries();
            if (res.success) {
                state.allQueries = res.data;
                filterQueries();
            }
        } catch (err) {
            console.error('Failed to load queries:', err);
        }
    }

    function filterQueries() {
        const query = state.searchQuery.toLowerCase();
        state.filteredQueries = state.allQueries.filter(q =>
            q.text.toLowerCase().includes(query)
        );
        ui.renderQueryList(state.filteredQueries, state.selectedQuery?.id);
    }

    async function handleSaveQuery(text, id) {
        if (!text) return;
        ui.setLoading(true);
        try {
            let res;
            if (id) {
                res = await api.updateQuery(id, text);
            } else {
                res = await api.addQuery(text);
            }

            if (res.success) {
                ui.hideModal();
                Swal.fire({
                    icon: 'success',
                    title: 'Berhasil',
                    text: id ? 'Query diperbarui' : 'Query ditambahkan',
                    timer: 1500,
                    showConfirmButton: false
                });
                await loadData();
            }
        } catch (e) {
            Swal.fire('Gagal', 'Terjadi kesalahan saat menyimpan query', 'error');
        } finally {
            ui.setLoading(false);
        }
    }

    async function handleDeleteQuery(id) {
        const result = await Swal.fire({
            title: 'Hapus Query?',
            text: 'Seluruh data evaluasi terkait akan hilang!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            confirmButtonText: 'Ya, Hapus'
        });

        if (result.isConfirmed) {
            ui.setLoading(true);
            try {
                const res = await api.deleteQuery(id);
                if (res.success) {
                    Swal.fire('Terhapus', 'Query telah dihapus', 'success');
                    if (state.selectedQuery?.id === id) {
                        state.selectedQuery = null;
                        document.getElementById('no-query-selected-v5').style.display = 'block';
                        document.getElementById('experiment-area-v5').style.display = 'none';
                    }
                    await loadData();
                }
            } catch (e) {
                Swal.fire('Gagal', 'Tidak dapat menghapus query', 'error');
            } finally {
                ui.setLoading(false);
            }
        }
    }

    function addRow() {
        if (state.rows.length >= 10) {
            Swal.fire({ icon: 'warning', title: 'Limit', text: 'Maksimum 10 baris' });
            return;
        }

        // Sequential Threshold Logic: 0.3, 0.4, 0.5...
        const threshold = Math.min(0.9, 0.3 + (state.rows.length * 0.1));
        const row = ui.createRow(state.rows.length + 1, threshold.toFixed(1));
        state.rows.push(row);
    }

    function resetBatch() {
        if (state.isRunning) return;
        state.rows = [];
        state.batchResults = [];
        ui.elements.batchContainer.innerHTML = '';
        ui.clearSummaryTable();
        for (let i = 0; i < 3; i++) addRow();
    }

    async function runBatch() {
        if (!state.selectedQuery || state.isRunning) return;

        state.isRunning = true;
        ui.setLoading(true);
        state.batchResults = [];
        ui.clearSummaryTable();

        try {
            // Filter out rows that might have been deleted by user from the DOM but still in state
            // Re-sync row list from DOM
            const activeRows = Array.from(ui.elements.batchContainer.querySelectorAll('.batch-row-v5'));

            await runner.executeSequential(state.selectedQuery, activeRows, (row, progress, result) => {
                ui.updateRowStatus(row, progress, result);

                // If row completed successfully, collect data for table/export
                if (progress === 100 && result && !result.error) {
                    const w2v = row.querySelector('[data-type="w2v"]').value;
                    const ft = row.querySelector('[data-type="ft"]').value;
                    const gv = row.querySelector('[data-type="gv"]').value;

                    state.batchResults.push({
                        w2v, ft, gv,
                        ...result
                    });
                }
            });

            if (state.batchResults.length > 0) {
                ui.renderSummaryTable(state.batchResults);
            }

            Swal.fire({
                icon: 'success',
                title: 'Batch Selesai',
                text: 'Eksperimen ensemble telah selesai.',
                toast: true,
                position: 'top-end',
                timer: 3000,
                showConfirmButton: false
            });
        } catch (err) {
            console.error(err);
        } finally {
            state.isRunning = false;
            ui.setLoading(false);
        }
    }

    function exportResults() {
        if (state.batchResults.length === 0) return;

        const data = state.batchResults.map((r, i) => ({
            'No': i + 1,
            'Topic': state.selectedQuery.text,
            'W2V_Threshold': r.w2v,
            'FT_Threshold': r.ft,
            'GV_Threshold': r.gv,
            'TP': r.true_positive,
            'FP': r.false_positive,
            'FN': r.false_negative,
            'Precision': r.precision.toFixed(4),
            'Recall': r.recall.toFixed(4),
            'F1_Score': r.f1.toFixed(4)
        }));

        const ws = XLSX.utils.json_to_sheet(data);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Evaluation Results");

        const filename = `Exp_V5_${state.selectedQuery.text.replace(/\s+/g, '_')}_${new Date().getTime()}.csv`;
        XLSX.writeFile(wb, filename);
    }

    // Initial Load
    loadData();
});
