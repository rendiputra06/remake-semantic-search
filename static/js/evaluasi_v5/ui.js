/**
 * Evaluation V5 - UI Component Manager (Glass Command Center Edition)
 */
export const ui = {
    elements: {
        queryList: document.getElementById('query-list-v5'),
        querySearch: document.getElementById('query-search-input'),
        queryTotalCount: document.getElementById('query-total-count'),
        btnAddQuery: document.getElementById('btn-add-query'),

        experimentArea: document.getElementById('experiment-area-v5'),
        noQuerySelected: document.getElementById('no-query-selected-v5'),
        activeQueryTitle: document.getElementById('active-query-title'),
        gtCount: document.getElementById('gt-count-v5'),

        batchContainer: document.getElementById('batch-container-v5'),
        btnAddRow: document.getElementById('btn-add-row-v5'),
        btnRunBatch: document.getElementById('btn-run-batch-v5'),
        btnResetBatch: document.getElementById('btn-reset-batch-v5'),
        btnExport: document.getElementById('btn-export-v5'),

        resultsContainer: document.getElementById('results-table-container-v5'),
        resultsTimestamp: document.getElementById('results-timestamp'),
        resultsTableBody: document.getElementById('summary-table-body-v5'),

        queryModal: new bootstrap.Modal(document.getElementById('queryModalV5')),
        queryModalTitle: document.getElementById('queryModalTitleV5'),
        formQuery: document.getElementById('form-query-v5'),
        queryTextInput: document.getElementById('query-text-input-v5'),
        queryIdHidden: document.getElementById('query-id-hidden-v5')
    },

    init({ onQuerySelect, onAddRow, onRunBatch, onResetBatch, onSearchQuery, onAddQuery, onEditQuery, onDeleteQuery, onExport }) {
        this.elements.btnAddRow.addEventListener('click', onAddRow);
        this.elements.btnRunBatch.addEventListener('click', onRunBatch);
        this.elements.btnResetBatch.addEventListener('click', onResetBatch);
        this.elements.btnExport.addEventListener('click', onExport);
        this.elements.querySearch.addEventListener('input', (e) => onSearchQuery(e.target.value));
        this.elements.btnAddQuery.addEventListener('click', onAddQuery);
        this.elements.formQuery.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = this.elements.queryTextInput.value.trim();
            const id = this.elements.queryIdHidden.value;
            onAddQuery(text, id);
        });

        this.onQuerySelect = onQuerySelect;
        this.onEditQuery = onEditQuery;
        this.onDeleteQuery = onDeleteQuery;
    },

    renderQueryList(queries, activeId = null) {
        this.elements.queryList.innerHTML = '';
        this.elements.queryTotalCount.innerText = queries.length;

        if (queries.length === 0) {
            this.elements.queryList.innerHTML = '<div class="text-center py-4 text-muted small">Tidak ada query ditemukan</div>';
            return;
        }

        queries.forEach(query => {
            const isActive = activeId === query.id;
            const div = document.createElement('div');
            div.className = `query-item-v5 ${isActive ? 'active' : ''}`;
            div.innerHTML = `
                <div class="text-truncate me-2">
                    <div class="fw-bold small">${query.text}</div>
                    <div class="text-muted" style="font-size: 0.65rem">ID: ${query.id}</div>
                </div>
                <div class="d-flex gap-1 opacity-ctrl">
                    <button class="btn btn-sm btn-link p-0 text-secondary btn-edit-q" title="Edit"><i class="fas fa-edit fa-xs"></i></button>
                    <button class="btn btn-sm btn-link p-0 text-danger btn-delete-q" title="Hapus"><i class="fas fa-trash fa-xs"></i></button>
                </div>
            `;

            div.onclick = (e) => {
                if (e.target.closest('button')) return;
                this.onQuerySelect(query);
            };

            div.querySelector('.btn-edit-q').onclick = (e) => {
                e.stopPropagation();
                this.onEditQuery(query);
            };

            div.querySelector('.btn-delete-q').onclick = (e) => {
                e.stopPropagation();
                this.onDeleteQuery(query.id);
            };

            this.elements.queryList.appendChild(div);
        });
    },

    showExperimentArea(query) {
        this.elements.noQuerySelected.style.display = 'none';
        this.elements.experimentArea.style.display = 'block';
        this.elements.activeQueryTitle.innerText = query.text;
    },

    updateGroundTruth(count) {
        this.elements.gtCount.innerText = count;
    },

    createRow(index, defaultValue = 0.5) {
        const row = document.createElement('div');
        row.className = 'glass-card batch-row-v5 p-3';
        row.id = `batch-row-${index}`;
        row.innerHTML = `
            <div class="row align-items-center">
                <div class="col-auto">
                    <div class="badge bg-light text-dark border fw-bold mb-2">#${index}</div>
                </div>
                <div class="col">
                    <div class="row g-2">
                        <div class="col-4">
                            <label class="small text-muted mb-1 d-block text-center">W2V Threshold</label>
                            <input type="number" step="0.05" min="0" max="1" class="form-control input-v5" value="${defaultValue}" data-type="w2v">
                        </div>
                        <div class="col-4">
                            <label class="small text-muted mb-1 d-block text-center">FT Threshold</label>
                            <input type="number" step="0.05" min="0" max="1" class="form-control input-v5" value="${defaultValue}" data-type="ft">
                        </div>
                        <div class="col-4">
                            <label class="small text-muted mb-1 d-block text-center">GV Threshold</label>
                            <input type="number" step="0.05" min="0" max="1" class="form-control input-v5" value="${defaultValue}" data-type="gv">
                        </div>
                    </div>
                </div>
                <div class="col-md-5">
                    <div class="metric-result mb-1 overflow-auto">
                        <span class="badge badge-v5 bg-secondary opacity-50">Siap</span>
                    </div>
                    <div class="progress-v5">
                        <div class="progress-bar-v5" id="progress-bar-${index}"></div>
                    </div>
                </div>
                <div class="col-auto">
                    <button class="btn btn-sm btn-link text-danger btn-remove-row" title="Hapus"><i class="fas fa-times-circle"></i></button>
                </div>
            </div>
        `;

        row.querySelector('.btn-remove-row').onclick = () => row.remove();
        this.elements.batchContainer.appendChild(row);
        return row;
    },

    updateRowStatus(row, progress, result = null) {
        const bar = row.querySelector('.progress-bar-v5');
        const metric = row.querySelector('.metric-result');

        bar.style.width = `${progress}%`;

        if (progress > 0 && progress < 100) {
            row.classList.add('active');
            metric.innerHTML = `<span class="badge badge-v5 bg-info border-info animate-pulse text-white">PROSES...</span>`;
        } else if (progress === 100) {
            row.classList.remove('active');
            row.classList.add('completed');
            if (result && !result.error) {
                // Formatting results like CSV: TP, FP, FN, Precision, Recall, F1
                metric.innerHTML = `
                    <div class="d-flex flex-wrap gap-2 justify-content-center" style="font-size: 0.7rem;">
                        <span class="badge bg-success-subtle text-success border border-success-subtle">TP: ${result.true_positive}</span>
                        <span class="badge bg-danger-subtle text-danger border border-danger-subtle">FP: ${result.false_positive}</span>
                        <span class="badge bg-warning-subtle text-warning border border-warning-subtle">FN: ${result.false_negative}</span>
                        <span class="text-primary fw-bold">P: ${result.precision.toFixed(3)}</span>
                        <span class="text-primary fw-bold">R: ${result.recall.toFixed(3)}</span>
                        <span class="text-primary fw-bold">F1: ${result.f1.toFixed(3)}</span>
                    </div>
                `;
            } else if (result && result.error) {
                metric.innerHTML = `<span class="badge badge-v5 bg-danger">ERROR</span>`;
            } else {
                metric.innerHTML = `<span class="badge badge-v5 bg-success">SELESAI</span>`;
            }
        }
    },

    showModal(title, text = '', id = '') {
        this.elements.queryModalTitle.innerText = title;
        this.elements.queryTextInput.value = text;
        this.elements.queryIdHidden.value = id;
        this.elements.queryModal.show();
    },

    hideModal() {
        this.elements.queryModal.hide();
    },

    clearSummaryTable() {
        this.elements.resultsTableBody.innerHTML = '';
        this.elements.resultsContainer.style.display = 'none';
        this.elements.btnExport.style.display = 'none';
    },

    renderSummaryTable(results) {
        this.elements.resultsContainer.style.display = 'block';
        this.elements.btnExport.style.display = 'block';
        this.elements.resultsTimestamp.innerText = `Terakhir dijalankan: ${new Date().toLocaleTimeString()}`;
        this.elements.resultsTableBody.innerHTML = '';

        results.forEach((res, idx) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="small fw-bold text-muted">${idx + 1}</td>
                <td class="small fw-bold">${res.w2v}</td>
                <td class="small fw-bold">${res.ft}</td>
                <td class="small fw-bold">${res.gv}</td>
                <td class="small text-success">${res.true_positive}</td>
                <td class="small text-danger">${res.false_positive}</td>
                <td class="small text-warning">${res.false_negative}</td>
                <td class="small">${res.precision.toFixed(4)}</td>
                <td class="small">${res.recall.toFixed(4)}</td>
                <td class="fw-bold text-primary">${res.f1.toFixed(4)}</td>
            `;
            this.elements.resultsTableBody.appendChild(tr);
        });
    },

    setLoading(isLoading) {
        this.elements.btnRunBatch.disabled = isLoading;
        this.elements.btnAddRow.disabled = isLoading;
        this.elements.btnResetBatch.disabled = isLoading;
        document.querySelectorAll('.input-v5').forEach(i => i.disabled = isLoading);
        document.querySelectorAll('.btn-remove-row').forEach(b => b.hidden = isLoading);
    }
};
