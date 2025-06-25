/**
 * Thesaurus Browse Manager
 * Handles browsing and filtering of thesaurus words
 */
class ThesaurusBrowseManager {
  constructor() {
    this.currentPage = 1;
    this.perPage = 20;
    this.sortBy = "word";
    this.filterType = "all";
    this.searchQuery = "";

    this.browseResults = document.getElementById("browseResults");
    this.browseStats = document.getElementById("browseStats");
    this.pagination = document.getElementById("pagination");
    this.sortBySelect = document.getElementById("sortBy");
    this.filterTypeSelect = document.getElementById("filterType");
    this.perPageSelect = document.getElementById("perPage");
    this.applyFiltersBtn = document.getElementById("applyFilters");
    this.browseSearch = document.getElementById("browseSearch");
    this.browseSearchBtn = document.getElementById("browseSearchBtn");

    this.initializeEventListeners();
    this.loadInitialData();
  }

  initializeEventListeners() {
    // Filter controls
    this.applyFiltersBtn.addEventListener("click", () => this.applyFilters());
    this.sortBySelect.addEventListener("change", () => this.applyFilters());
    this.filterTypeSelect.addEventListener("change", () => this.applyFilters());
    this.perPageSelect.addEventListener("change", () => this.applyFilters());

    // Search
    this.browseSearchBtn.addEventListener("click", () => this.searchWords());
    this.browseSearch.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.searchWords();
    });
  }

  async loadInitialData() {
    try {
      await Promise.all([this.loadBrowseStats(), this.loadWords()]);
    } catch (error) {
      console.error("Error loading initial data:", error);
      this.showAlert("warning", "Gagal memuat data awal");
    }
  }

  async loadBrowseStats() {
    try {
      const response = await fetch("/api/public/thesaurus/stats");
      const data = await response.json();

      if (data.success) {
        this.displayBrowseStats(data.data);
      }
    } catch (error) {
      console.error("Error loading browse stats:", error);
    }
  }

  displayBrowseStats(stats) {
    // Extract relation counts from relation_distribution
    const relationCounts = {};
    stats.relation_distribution.forEach(rel => {
      relationCounts[rel.relation_type] = rel.count;
    });

    const html = `
            <div class="row text-center">
                <div class="col-4">
                    <div class="h4 text-primary">${stats.basic_stats.unique_words.toLocaleString()}</div>
                    <small class="text-muted">Total Kata</small>
                </div>
                <div class="col-4">
                    <div class="h4 text-success">${stats.basic_stats.total_relations.toLocaleString()}</div>
                    <small class="text-muted">Total Relasi</small>
                </div>
                <div class="col-4">
                    <div class="h4 text-info">${stats.basic_stats.avg_score.toFixed(2)}</div>
                    <small class="text-muted">Skor Rata-rata</small>
                </div>
            </div>
            <hr>
            <div class="small">
                <div class="mb-1">
                    <strong>Sinonim:</strong> ${(relationCounts.synonym || 0).toLocaleString()}
                </div>
                <div class="mb-1">
                    <strong>Antonim:</strong> ${(relationCounts.antonym || 0).toLocaleString()}
                </div>
                <div class="mb-1">
                    <strong>Hiponim:</strong> ${(relationCounts.hyponym || 0).toLocaleString()}
                </div>
                <div class="mb-1">
                    <strong>Hipernim:</strong> ${(relationCounts.hypernym || 0).toLocaleString()}
                </div>
            </div>
        `;

    this.browseStats.innerHTML = html;
  }

  async loadWords() {
    this.showLoading();

    try {
      const params = new URLSearchParams({
        page: this.currentPage,
        per_page: this.perPage,
        sort_by: this.sortBy,
        filter_type: this.filterType
      });

      const response = await fetch(`/api/public/thesaurus/browse?${params}`);
      const data = await response.json();

      if (data.success) {
        this.displayWords(data.data.words, data.data.pagination);
      } else {
        this.showAlert("danger", data.message || "Gagal memuat daftar kata");
      }
    } catch (error) {
      console.error("Error loading words:", error);
      this.showAlert("danger", "Terjadi kesalahan saat memuat data");
    } finally {
      this.hideLoading();
    }
  }

  displayWords(words, pagination) {
    if (words.length === 0) {
      this.browseResults.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">Tidak ada kata yang ditemukan</h5>
                    <p class="text-muted">Coba ubah filter atau kata kunci pencarian</p>
                </div>
            `;
      this.pagination.innerHTML = '';
      return;
    }

    let html = '<div class="row">';

    words.forEach((word) => {
      html += `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h5 class="card-title mb-0">
                                    <a href="/thesaurus/word/${encodeURIComponent(word.word)}" 
                                       class="text-decoration-none">${word.word}</a>
                                </h5>
                                <span class="badge bg-primary">${word.relation_count}</span>
                            </div>
                            ${word.definition ? `
                            <p class="card-text small text-muted mb-2">
                                ${word.definition}
                            </p>
                            ` : ''}
                            <div class="small text-muted mb-3">
                                <div><i class="fas fa-link"></i> ${word.relation_count} relasi</div>
                            </div>
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="browseManager.viewWord('${word.word}')">
                                <i class="fas fa-eye"></i> Lihat Detail
                            </button>
                        </div>
                    </div>
                </div>
            `;
    });

    html += '</div>';
    this.browseResults.innerHTML = html;

    // Update pagination
    this.displayPagination({
      current_page: pagination.page,
      total_pages: pagination.pages,
      total: pagination.total
    });
  }

  displayPagination(pagination) {
    if (!pagination || pagination.total_pages <= 1) {
      this.pagination.innerHTML = '';
      return;
    }

    const currentPage = pagination.current_page;
    const totalPages = pagination.total_pages;
    let html = '';

    // Previous button
    html += `
      <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); browseManager.goToPage(${currentPage - 1})">
          <i class="fas fa-chevron-left"></i>
        </a>
      </li>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 || // First page
        i === totalPages || // Last page
        (i >= currentPage - 2 && i <= currentPage + 2) // Pages around current
      ) {
        html += `
          <li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); browseManager.goToPage(${i})">${i}</a>
          </li>
        `;
      } else if (
        (i === currentPage - 3 && currentPage > 4) ||
        (i === currentPage + 3 && currentPage < totalPages - 3)
      ) {
        html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
      }
    }

    // Next button
    html += `
      <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); browseManager.goToPage(${currentPage + 1})">
          <i class="fas fa-chevron-right"></i>
        </a>
      </li>
    `;

    this.pagination.innerHTML = html;
  }

  applyFilters() {
    this.currentPage = 1;
    this.sortBy = this.sortBySelect.value;
    this.filterType = this.filterTypeSelect.value;
    this.perPage = parseInt(this.perPageSelect.value);
    this.loadWords();
  }

  searchWords() {
    const query = this.browseSearch.value.trim();
    if (query) {
      // Redirect to search page or use search endpoint
      window.location.href = `/thesaurus?word=${encodeURIComponent(query)}`;
    }
  }

  goToPage(page) {
    this.currentPage = page;
    this.loadWords();
  }

  viewWord(word) {
    window.location.href = `/thesaurus/word/${encodeURIComponent(word)}`;
  }

  showLoading() {
    this.browseResults.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Memuat daftar kata...</p>
            </div>
        `;
  }

  hideLoading() {
    // Loading is handled by displayWords
  }

  showAlert(type, message) {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    this.browseResults.parentNode.insertBefore(alertDiv, this.browseResults);

    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.browseManager = new ThesaurusBrowseManager();
});
