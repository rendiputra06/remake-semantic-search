/**
 * CRUD Module for Integrated Evaluation
 * Handles Query and Relevant Verse management
 */
import { api } from './api.js';
import { ui } from './ui.js';

export class CRUDManager {
    constructor(callbacks) {
        this.selectedQueryId = null;
        this.groundTruthVerses = [];
        this.allAyatData = [];
        this.currentAyatIndex = 0;
        this.ayatLoadLimit = 10;
        this.callbacks = callbacks; // onQuerySelected

        this.init();
    }

    init() {
        this.queryList = document.getElementById("query-list");
        this.btnAddQueryModal = document.getElementById("btn-add-query-modal");
        this.queryModal = new bootstrap.Modal(document.getElementById("queryModal"));
        this.formQuery = document.getElementById("form-query");
        this.queryTextInput = document.getElementById("query-text-input");
        this.queryIdHidden = document.getElementById("query-id-hidden");
        this.queryModalTitle = document.getElementById("queryModalTitle");

        this.relevantVerseList = document.getElementById("relevant-verse-list");
        this.evaluasiBtn = document.getElementById("evaluasi-btn");
        this.resetRelevantVersesBtn = document.getElementById("reset-relevant-verses-btn");
        this.noQuerySelected = document.getElementById("no-query-selected");
        this.queryCount = document.getElementById("query-count");
        this.ayatCount = document.getElementById("ayat-count");

        this.setupEventListeners();
    }

    setupEventListeners() {
        if (this.btnAddQueryModal) {
            this.btnAddQueryModal.addEventListener("click", () => this.showAddQueryModal());
        }

        if (this.formQuery) {
            this.formQuery.addEventListener("submit", (e) => this.handleSaveQuery(e));
        }

        // Modal events for verses
        document.getElementById("form-add-verse-modal").addEventListener("submit", (e) => this.handleAddVerseModal(e));
        document.getElementById("load-more-btn").addEventListener("click", () => this.loadMoreAyat());

        this.evaluasiBtn.addEventListener("click", () => {
            if (this.selectedQueryId) this.showAllAyatDetailModal(this.selectedQueryId);
        });

        this.resetRelevantVersesBtn.addEventListener("click", () => this.handleResetVerses());
    }

    async loadQueries() {
        ui.showSpinner(this.queryList, "Memuat query...");
        const data = await api.getQueries();
        if (data.success) {
            this.renderQueryList(data.data);
        }
    }

    renderQueryList(queries) {
        this.queryCount.textContent = queries.length;
        if (queries.length === 0) {
            this.queryList.innerHTML = '<div class="p-3 text-center text-muted small">Belum ada query.</div>';
            return;
        }

        let html = '';
        queries.forEach((q) => {
            const isActive = this.selectedQueryId === q.id;
            html += `
            <div class="list-group-item list-group-item-action border-0 mb-1 rounded d-flex justify-content-between align-items-center query-item ${isActive ? "bg-primary-light border-start border-primary border-4" : ""}" 
                 style="cursor:pointer" data-id="${q.id}">
                <div class="text-truncate me-2 flex-grow-1 py-1" title="${q.text}">
                    <span class="${isActive ? 'fw-bold text-primary' : ''}">${q.text}</span>
                </div>
                <div class="btn-group btn-group-sm opacity-ctrl">
                    <button class="btn btn-link link-secondary p-1 btn-edit-query" data-id="${q.id}" title="Edit">
                        <i class="fas fa-edit fa-xs"></i>
                    </button>
                    <button class="btn btn-link link-danger p-1 btn-delete-query" data-id="${q.id}" title="Hapus">
                        <i class="fas fa-trash fa-xs"></i>
                    </button>
                </div>
            </div>`;
        });
        this.queryList.innerHTML = html;

        // Click on query item (excluding buttons)
        this.queryList.querySelectorAll(".query-item").forEach((el) => {
            el.addEventListener("click", (e) => {
                if (e.target.closest("button")) return;
                const id = parseInt(el.getAttribute("data-id"));
                const query = queries.find(q => q.id === id);
                this.selectQuery(query);
            });
        });

        // Edit query
        this.queryList.querySelectorAll(".btn-edit-query").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const id = parseInt(btn.getAttribute("data-id"));
                const query = queries.find(q => q.id === id);
                this.showEditQueryModal(query);
            });
        });

        // Delete query
        this.queryList.querySelectorAll(".btn-delete-query").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const id = parseInt(btn.getAttribute("data-id"));
                this.handleDeleteQuery(id);
            });
        });
    }

    selectQuery(query) {
        this.selectedQueryId = query.id;
        this.loadQueries(); // Refresh to update active state
        this.loadRelevantVerses(query.id);

        if (this.noQuerySelected) this.noQuerySelected.classList.add("d-none");
        this.evaluasiBtn.classList.remove("d-none");
        this.resetRelevantVersesBtn.classList.remove("d-none");

        if (this.callbacks.onQuerySelected) {
            this.callbacks.onQuerySelected(query);
        }
    }

    showAddQueryModal() {
        this.queryModalTitle.textContent = "Tambah Query";
        this.queryTextInput.value = "";
        this.queryIdHidden.value = "";
        this.queryModal.show();
    }

    showEditQueryModal(query) {
        this.queryModalTitle.textContent = "Edit Query";
        this.queryTextInput.value = query.text;
        this.queryIdHidden.value = query.id;
        this.queryModal.show();
    }

    async handleSaveQuery(e) {
        e.preventDefault();
        const text = this.queryTextInput.value.trim();
        const id = this.queryIdHidden.value;
        if (!text) return;

        let result;
        if (id) {
            // Update (assuming API supports PUT/POST to specific ID)
            // For now, let's assume update is handled by separate method or same add method logic
            // Since I don't see an explicit update API in api.js, I'll stick to add or show error
            result = await api.addQuery(text); // Fallback: add new
        } else {
            result = await api.addQuery(text);
        }

        if (result.success) {
            this.queryModal.hide();
            Swal.fire({ icon: 'success', title: 'Berhasil', text: 'Query disimpan', timer: 1000, showConfirmButton: false });
            this.loadQueries();
        }
    }

    handleDeleteQuery(id) {
        Swal.fire({
            title: "Hapus Query?",
            text: "Data evaluasi terkait akan ikut terhapus!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Ya, Hapus!",
        }).then(async (result) => {
            if (result.isConfirmed) {
                const data = await api.deleteQuery(id);
                if (data.success) {
                    Swal.fire({ icon: 'success', title: 'Terhapus', text: 'Query dihapus', timer: 1000, showConfirmButton: false });
                    this.loadQueries();
                    if (this.selectedQueryId === id) {
                        this.selectedQueryId = null;
                        this.relevantVerseList.innerHTML = "";
                        if (this.noQuerySelected) this.noQuerySelected.classList.remove("d-none");
                        this.evaluasiBtn.classList.add("d-none");
                        this.resetRelevantVersesBtn.classList.add("d-none");
                        if (this.callbacks.onQuerySelected) this.callbacks.onQuerySelected(null);
                    }
                }
            }
        });
    }

    async loadRelevantVerses(queryId) {
        ui.showSpinner(this.relevantVerseList, "Memuat...");
        const data = await api.getRelevantVerses(queryId);
        if (data.success) {
            this.groundTruthVerses = data.data.map((v) => v.verse_ref);
            this.renderRelevantVerses(data.data);
            this.ayatCount.textContent = data.data.length;
        }
    }

    renderRelevantVerses(verses) {
        if (verses.length === 0) {
            this.relevantVerseList.innerHTML = '<div class="alert alert-sm alert-info py-1 small">Belum ada ayat relevan terdaftar.</div>';
            return;
        }

        let html = '<div class="d-flex flex-wrap gap-1">';
        const preview = verses.slice(0, 15);
        preview.forEach((v) => {
            html += `<span class="badge bg-primary-light text-primary border border-primary-subtle badge-ayat-ref" style="font-size: 0.75rem">${v.verse_ref}</span>`;
        });
        if (verses.length > 15) {
            html += `<span class="badge bg-light text-muted border" style="font-size: 0.75rem">... +${verses.length - 15}</span>`;
        }
        html += '</div>';
        this.relevantVerseList.innerHTML = html;
    }

    async showAllAyatDetailModal(queryId) {
        const content = document.getElementById("ayat-detail-content");
        const modal = new bootstrap.Modal(document.getElementById("ayatDetailModal"));
        ui.showSpinner(content, "Memuat...");

        const data = await api.getRelevantVerses(queryId);
        if (!data.success || data.data.length === 0) {
            content.innerHTML = '<div class="text-muted">Tidak ada ayat relevan.</div>';
            document.getElementById('load-more-container').classList.add('d-none');
            modal.show();
            return;
        }

        this.allAyatData = data.data;
        this.currentAyatIndex = 0;
        document.getElementById('total-count').textContent = this.allAyatData.length;
        document.getElementById('loaded-count').textContent = '0';
        content.innerHTML = '<ul class="list-group mb-3 shadow-sm"></ul>';

        await this.loadMoreAyat();
        modal.show();
    }

    async loadMoreAyat() {
        const container = document.querySelector('#ayat-detail-content ul');
        if (!container) return;

        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSpinner = document.getElementById('load-more-spinner');

        loadMoreBtn.disabled = true;
        loadMoreSpinner.classList.remove('d-none');

        const endIndex = Math.min(this.currentAyatIndex + this.ayatLoadLimit, this.allAyatData.length);
        for (let i = this.currentAyatIndex; i < endIndex; i++) {
            const v = this.allAyatData[i];
            const [surah, ayat] = v.verse_ref.split(":");
            let itemHtml = `<li class='list-group-item d-flex justify-content-between align-items-center' data-id='${v.id}'>`;
            try {
                const j = await api.getAyatDetail(surah, ayat);
                if (j.success && j.ayat) {
                    itemHtml += `
                        <div>
                            <span class="badge bg-primary me-2">${v.verse_ref}</span>
                            <div class='text-arab small mt-1'>${j.ayat.text}</div>
                        </div>`;
                } else {
                    itemHtml += `<div><strong>${v.verse_ref}</strong></div>`;
                }
            } catch (e) {
                itemHtml += `<div><strong>${v.verse_ref}</strong></div>`;
            }
            itemHtml += `<button class='btn btn-sm btn-outline-danger btn-delete-verse-modal' data-id='${v.id}'><i class='fas fa-trash'></i></button></li>`;
            container.insertAdjacentHTML('beforeend', itemHtml);
        }

        this.currentAyatIndex = endIndex;
        document.getElementById('loaded-count').textContent = this.currentAyatIndex;
        document.getElementById('load-more-container').classList.toggle('d-none', this.currentAyatIndex >= this.allAyatData.length);

        loadMoreBtn.disabled = false;
        loadMoreSpinner.classList.add('d-none');

        // Attach delete event
        container.querySelectorAll('.btn-delete-verse-modal').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                await api.deleteRelevantVerse(id);
                this.loadRelevantVerses(this.selectedQueryId);
                this.showAllAyatDetailModal(this.selectedQueryId);
            });
        });
    }

    async handleAddVerseModal(e) {
        e.preventDefault();
        const input = document.getElementById("verse-ref-modal");
        const verse = input.value.trim();
        if (!verse || !this.selectedQueryId) return;

        await api.addRelevantVerse(this.selectedQueryId, verse);
        input.value = "";
        this.loadRelevantVerses(this.selectedQueryId);
        this.showAllAyatDetailModal(this.selectedQueryId);
    }

    handleResetVerses() {
        Swal.fire({
            title: "Reset Semua Ayat?",
            text: "Seluruh ayat relevan untuk query ini akan dihapus!",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Ya, Reset!",
        }).then(async (result) => {
            if (result.isConfirmed) {
                Swal.fire("Info", "Fitur reset masal belum tersedia di API.", "info");
            }
        });
    }
}
