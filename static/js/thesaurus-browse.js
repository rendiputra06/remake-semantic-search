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
    const html = `
            <div class="row text-center">
                <div class="col-6">
                    <div class="h4 text-primary">${stats.total_words}</div>
                    <small class="text-muted">Total Kata</small>
                </div>
                <div class="col-6">
                    <div class="h4 text-success">${stats.total_relations}</div>
                    <small class="text-muted">Total Relasi</small>
                </div>
            </div>
            <hr>
            <div class="small">
                <div class="mb-1">
                    <strong>Sinonim:</strong> ${
                      stats.relation_counts.synonym || 0
                    }
                </div>
                <div class="mb-1">
                    <strong>Antonim:</strong> ${
                      stats.relation_counts.antonym || 0
                    }
                </div>
                <div class="mb-1">
                    <strong>Hiponim:</strong> ${
                      stats.relation_counts.hyponym || 0
                    }
                </div>
                <div class="mb-1">
                    <strong>Hipernim:</strong> ${
                      stats.relation_counts.hypernym || 0
                    }
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
        filter_type: this.filterType,
        search: this.searchQuery,
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
      return;
    }

    let html = '<div class="row">';

    words.forEach((word, index) => {
      const relationCount = word.relation_count || 0;
      const avgScore = word.avg_score ? word.avg_score.toFixed(2) : "0.00";

      html += `
                <div class="col-md-6 col-lg-4 mb-3">
                    <div class="card thesaurus-card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">
                                    <a href="/thesaurus/word/${encodeURIComponent(
                                      word.word
                                    )}" 
                                       class="word-link">${word.word}</a>
                                </h6>
                                <span class="badge bg-primary">${relationCount}</span>
                            </div>
                            <div class="small text-muted">
                                <div class="mb-1">
                                    <i class="fas fa-chart-line"></i> Skor: ${avgScore}
                                </div>
                                <div class="mb-1">
                                    <i class="fas fa-link"></i> ${relationCount} relasi
                                </div>
                            </div>
                            <div class="mt-2">
                                <button class="btn btn-sm btn-outline-primary" 
                                        onclick="browseManager.viewWord('${
                                          word.word
                                        }')">
                                    <i class="fas fa-eye"></i> Lihat Detail
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    });

    html += "</div>";
    this.browseResults.innerHTML = html;

    this.displayPagination(pagination);
  }

  displayPagination(pagination) {
    if (!pagination || pagination.total_pages <= 1) {
      this.pagination.innerHTML = "";
      return;
    }

    let html = "";
    const currentPage = pagination.current_page;
    const totalPages = pagination.total_pages;

    // Previous button
    html += `
            <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
                <a class="page-link" href="#" onclick="browseManager.goToPage(${
                  currentPage - 1
                })">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      html += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="browseManager.goToPage(1)">1</a>
                </li>
            `;
      if (startPage > 2) {
        html +=
          '<li class="page-item disabled"><span class="page-link">...</span></li>';
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      html += `
                <li class="page-item ${i === currentPage ? "active" : ""}">
                    <a class="page-link" href="#" onclick="browseManager.goToPage(${i})">${i}</a>
                </li>
            `;
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        html +=
          '<li class="page-item disabled"><span class="page-link">...</span></li>';
      }
      html += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="browseManager.goToPage(${totalPages})">${totalPages}</a>
                </li>
            `;
    }

    // Next button
    html += `
            <li class="page-item ${
              currentPage === totalPages ? "disabled" : ""
            }">
                <a class="page-link" href="#" onclick="browseManager.goToPage(${
                  currentPage + 1
                })">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;

    this.pagination.innerHTML = html;
  }

  applyFilters() {
    this.sortBy = this.sortBySelect.value;
    this.filterType = this.filterTypeSelect.value;
    this.perPage = parseInt(this.perPageSelect.value);
    this.currentPage = 1;
    this.loadWords();
  }

  searchWords() {
    this.searchQuery = this.browseSearch.value.trim();
    this.currentPage = 1;
    this.loadWords();
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
