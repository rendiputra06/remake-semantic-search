/**
 * Public Thesaurus Manager
 * Handles all interactions for the public thesaurus page
 */
class PublicThesaurusManager {
  constructor() {
    this.searchInput = document.getElementById("thesaurusSearch");
    this.searchBtn = document.getElementById("searchBtn");
    this.searchResults = document.getElementById("searchResults");
    this.searchSuggestions = document.getElementById("searchSuggestions");
    this.thesaurusStats = document.getElementById("thesaurusStats");
    this.popularWords = document.getElementById("popularWords");
    this.randomWords = document.getElementById("randomWords");
    this.refreshRandomBtn = document.getElementById("refreshRandom");
    this.loadingModal = new bootstrap.Modal(
      document.getElementById("loadingModal")
    );

    this.searchTimeout = null;
    this.initializeEventListeners();
    this.loadInitialData();
  }

  initializeEventListeners() {
    // Search functionality
    this.searchBtn.addEventListener("click", () => this.searchWord());
    this.searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.searchWord();
    });

    // Auto-suggestions
    this.searchInput.addEventListener("input", (e) => {
      this.handleSearchInput(e.target.value);
    });

    // Hide suggestions when clicking outside
    document.addEventListener("click", (e) => {
      if (
        !this.searchInput.contains(e.target) &&
        !this.searchSuggestions.contains(e.target)
      ) {
        this.hideSuggestions();
      }
    });

    // Random words refresh
    this.refreshRandomBtn.addEventListener("click", () =>
      this.loadRandomWords()
    );
  }

  async loadInitialData() {
    try {
      await Promise.all([
        this.loadStatistics(),
        this.loadPopularWords(),
        this.loadRandomWords(),
      ]);
    } catch (error) {
      console.error("Error loading initial data:", error);
      this.showAlert("warning", "Gagal memuat data awal");
    }
  }

  handleSearchInput(value) {
    clearTimeout(this.searchTimeout);

    if (value.length < 2) {
      this.hideSuggestions();
      return;
    }

    this.searchTimeout = setTimeout(() => {
      this.loadSearchSuggestions(value);
    }, 300);
  }

  async loadSearchSuggestions(query) {
    try {
      const response = await fetch(
        `/api/public/thesaurus/suggestions?q=${encodeURIComponent(
          query
        )}&limit=10`
      );
      const data = await response.json();

      if (data.success && data.data.suggestions.length > 0) {
        this.showSuggestions(data.data.suggestions);
      } else {
        this.hideSuggestions();
      }
    } catch (error) {
      console.error("Error loading suggestions:", error);
      this.hideSuggestions();
    }
  }

  showSuggestions(suggestions) {
    let html = "";
    suggestions.forEach((suggestion) => {
      html += `
                <a href="#" class="list-group-item list-group-item-action suggestion-item" data-word="${suggestion}">
                    <i class="fas fa-search me-2"></i>${suggestion}
                </a>
            `;
    });

    this.searchSuggestions.innerHTML = html;
    this.searchSuggestions.style.display = "block";

    // Add click handlers for suggestions
    document.querySelectorAll(".suggestion-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        e.preventDefault();
        this.searchInput.value = item.dataset.word;
        this.hideSuggestions();
        this.searchWord();
      });
    });
  }

  hideSuggestions() {
    this.searchSuggestions.style.display = "none";
  }

  async searchWord() {
    const word = this.searchInput.value.trim();
    if (!word) {
      this.showAlert("warning", "Masukkan kata yang ingin dicari");
      return;
    }

    this.showLoading();

    try {
      const response = await fetch(
        `/api/public/thesaurus/search?word=${encodeURIComponent(word)}`
      );
      const data = await response.json();

      if (data.success) {
        this.displaySearchResults(word, data.data.results);
      } else {
        this.showAlert("danger", data.message || "Gagal mencari kata");
      }
    } catch (error) {
      console.error("Error searching:", error);
      this.showAlert("danger", "Terjadi kesalahan saat mencari");
    } finally {
      this.hideLoading();
    }
  }

  displaySearchResults(word, results) {
    this.searchResults.classList.remove("d-none");

    let html = `
            <div class="card thesaurus-card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-search"></i> Hasil Pencarian: "${word}"
                    </h5>
                </div>
                <div class="card-body">
        `;

    // Display synonyms
    if (results.synonyms && results.synonyms.length > 0) {
      html += `
                <div class="mb-4">
                    <h6 class="text-success">
                        <i class="fas fa-sync-alt"></i> Sinonim (${results.synonyms.length})
                    </h6>
                    <div class="row">
            `;

      results.synonyms.forEach((synonym) => {
        html += `
                    <div class="col-md-6 mb-2">
                        <div class="card border-success">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong class="word-link" onclick="thesaurusManager.searchWord('${
                                      synonym.word
                                    }')">${synonym.word}</strong>
                                    <span class="badge bg-success relation-badge">${synonym.score.toFixed(
                                      2
                                    )}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
      });

      html += "</div></div>";
    }

    // Display other relation types if available
    const otherTypes = ["antonyms", "hyponyms", "hypernyms"];
    const typeConfigs = {
      antonyms: {
        label: "Antonim",
        icon: "fas fa-exchange-alt",
        color: "danger",
      },
      hyponyms: { label: "Hiponim", icon: "fas fa-arrow-down", color: "info" },
      hypernyms: {
        label: "Hipernim",
        icon: "fas fa-arrow-up",
        color: "warning",
      },
    };

    otherTypes.forEach((type) => {
      if (results[type] && results[type].length > 0) {
        const config = typeConfigs[type];
        html += `
                    <div class="mb-4">
                        <h6 class="text-${config.color}">
                            <i class="${config.icon}"></i> ${config.label} (${results[type].length})
                        </h6>
                        <div class="row">
                `;

        results[type].forEach((item) => {
          html += `
                        <div class="col-md-6 mb-2">
                            <div class="card border-${config.color}">
                                <div class="card-body p-3">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong class="word-link" onclick="thesaurusManager.searchWord('${
                                          item.word
                                        }')">${item.word}</strong>
                                        <span class="badge bg-${
                                          config.color
                                        } relation-badge">${item.score.toFixed(
            2
          )}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
        });

        html += "</div></div>";
      }
    });

    if (
      (!results.synonyms || results.synonyms.length === 0) &&
      (!results.antonyms || results.antonyms.length === 0) &&
      (!results.hyponyms || results.hyponyms.length === 0) &&
      (!results.hypernyms || results.hypernyms.length === 0)
    ) {
      html += `
                <div class="text-center py-4">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <p class="text-muted">Tidak ditemukan relasi untuk kata "${word}"</p>
                    <p class="text-muted small">Coba kata lain atau periksa ejaan</p>
                </div>
            `;
    }

    html += "</div></div>";
    this.searchResults.innerHTML = html;
  }

  async loadStatistics() {
    try {
      const response = await fetch("/api/public/thesaurus/statistics");
      const data = await response.json();

      if (data.success) {
        const stats = data.data;
        this.thesaurusStats.innerHTML = `
                    <div class="row text-center">
                        <div class="col-4">
                            <h4 class="text-white">${stats.basic_stats.unique_words.toLocaleString()}</h4>
                            <small class="text-light">Kata Unik</small>
                        </div>
                        <div class="col-4">
                            <h4 class="text-white">${stats.basic_stats.total_relations.toLocaleString()}</h4>
                            <small class="text-light">Total Relasi</small>
                        </div>
                        <div class="col-4">
                            <h4 class="text-white">${
                              stats.basic_stats.avg_score
                            }</h4>
                            <small class="text-light">Skor Rata-rata</small>
                        </div>
                    </div>
                `;
      }
    } catch (error) {
      console.error("Error loading statistics:", error);
      this.thesaurusStats.innerHTML =
        '<p class="text-light text-center">Gagal memuat statistik</p>';
    }
  }

  async loadPopularWords() {
    try {
      const response = await fetch("/api/public/thesaurus/popular?limit=10");
      const data = await response.json();

      if (data.success) {
        let html = "";
        data.data.words.forEach((word, index) => {
          html += `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="text-truncate word-link" onclick="thesaurusManager.searchWord('${
                              word.word
                            }')">
                                ${index + 1}. ${word.word}
                            </span>
                            <span class="badge bg-primary">${
                              word.relation_count
                            }</span>
                        </div>
                    `;
        });
        this.popularWords.innerHTML = html;
      }
    } catch (error) {
      console.error("Error loading popular words:", error);
      this.popularWords.innerHTML =
        '<p class="text-center text-muted">Gagal memuat kata populer</p>';
    }
  }

  async loadRandomWords() {
    try {
      const response = await fetch("/api/public/thesaurus/random?count=5");
      const data = await response.json();

      if (data.success) {
        let html = "";
        data.data.words.forEach((word) => {
          html += `
                        <div class="mb-2">
                            <a href="#" class="text-decoration-none word-link random-word" data-word="${word.word}">
                                <i class="fas fa-random me-1"></i>${word.word}
                            </a>
                        </div>
                    `;
        });
        this.randomWords.innerHTML = html;

        // Add click handlers for random words
        document.querySelectorAll(".random-word").forEach((link) => {
          link.addEventListener("click", (e) => {
            e.preventDefault();
            this.searchInput.value = link.dataset.word;
            this.searchWord();
          });
        });
      }
    } catch (error) {
      console.error("Error loading random words:", error);
      this.randomWords.innerHTML =
        '<p class="text-center text-muted">Gagal memuat kata acak</p>';
    }
  }

  showLoading() {
    this.loadingModal.show();
  }

  hideLoading() {
    this.loadingModal.hide();
  }

  showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText =
      "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.appendChild(alertDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }
}

// Initialize when document is ready
let thesaurusManager;
document.addEventListener("DOMContentLoaded", () => {
  thesaurusManager = new PublicThesaurusManager();
});
