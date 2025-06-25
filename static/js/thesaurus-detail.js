/**
 * Thesaurus Detail Manager
 * Handles word detail page functionality
 */
class ThesaurusDetailManager {
  constructor() {
    this.word = this.getWordFromUrl();
    this.wordDetail = document.getElementById("wordDetail");
    this.wordInfo = document.getElementById("wordInfo");
    this.relatedWords = document.getElementById("relatedWords");
    this.searchSimilarBtn = document.getElementById("searchSimilar");
    this.exportWordBtn = document.getElementById("exportWord");
    this.similarWordsModal = new bootstrap.Modal(
      document.getElementById("similarWordsModal")
    );
    this.similarWordsContent = document.getElementById("similarWordsContent");

    this.initializeEventListeners();
    this.loadWordDetail();
  }

  getWordFromUrl() {
    const pathParts = window.location.pathname.split("/");
    return decodeURIComponent(pathParts[pathParts.length - 1]);
  }

  initializeEventListeners() {
    this.searchSimilarBtn.addEventListener("click", () =>
      this.searchSimilarWords()
    );
    this.exportWordBtn.addEventListener("click", () => this.exportWordData());
  }

  async loadWordDetail() {
    try {
      const response = await fetch(
        `/api/public/thesaurus/search?word=${encodeURIComponent(this.word)}`
      );
      const data = await response.json();

      if (data.success) {
        this.displayWordDetail(data.data.results);
        this.loadWordInfo(data.data.results);
        this.loadRelatedWords(data.data.results);
      } else {
        this.showWordNotFound();
      }
    } catch (error) {
      console.error("Error loading word detail:", error);
      this.showWordNotFound();
    }
  }

  displayWordDetail(wordData) {
    let html = `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-book-open"></i> Detail Kata: "${this.word}"
                    </h5>
                </div>
                <div class="card-body">
        `;

    // Display synonyms
    if (wordData.synonyms && wordData.synonyms.length > 0) {
      html += this.createRelationSection(
        "synonym",
        "Sinonim",
        wordData.synonyms
      );
    }

    // Display antonyms
    if (wordData.antonyms && wordData.antonyms.length > 0) {
      html += this.createRelationSection(
        "antonym",
        "Antonim",
        wordData.antonyms
      );
    }

    // Display hyponyms
    if (wordData.hyponyms && wordData.hyponyms.length > 0) {
      html += this.createRelationSection(
        "hyponym",
        "Hiponim",
        wordData.hyponyms
      );
    }

    // Display hypernyms
    if (wordData.hypernyms && wordData.hypernyms.length > 0) {
      html += this.createRelationSection(
        "hypernym",
        "Hipernim",
        wordData.hypernyms
      );
    }

    // If no relations found
    if (
      !wordData.synonyms?.length &&
      !wordData.antonyms?.length &&
      !wordData.hyponyms?.length &&
      !wordData.hypernyms?.length
    ) {
      html += `
                <div class="text-center text-muted">
                    <i class="fas fa-info-circle fa-3x mb-3"></i>
                    <h5>Tidak ada relasi ditemukan</h5>
                    <p>Kata "${this.word}" belum memiliki relasi dalam tesaurus</p>
                </div>
            `;
    }

    html += "</div></div>";
    this.wordDetail.innerHTML = html;
  }

  createRelationSection(type, title, relations) {
    let html = `
            <div class="relation-section ${type} mb-4">
                <h6 class="text-${this.getRelationColor(type)}">
                    <i class="fas fa-${this.getRelationIcon(
                      type
                    )}"></i> ${title} (${relations.length})
                </h6>
                <div class="row">
        `;

    relations.forEach((relation) => {
      const score = relation.score ? relation.score.toFixed(2) : "0.00";
      html += `
                <div class="col-md-6 col-lg-4 mb-2">
                    <div class="card border-${this.getRelationColor(type)}">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <strong class="word-link" onclick="detailManager.searchWord('${
                                  relation.word
                                }')">
                                    ${relation.word}
                                </strong>
                                <span class="badge bg-${this.getRelationColor(
                                  type
                                )} relation-badge">
                                    ${score}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    });

    html += "</div></div>";
    return html;
  }

  getRelationColor(type) {
    const colors = {
      synonym: "success",
      antonym: "danger",
      hyponym: "warning",
      hypernym: "info",
    };
    return colors[type] || "primary";
  }

  getRelationIcon(type) {
    const icons = {
      synonym: "sync-alt",
      antonym: "exchange-alt",
      hyponym: "arrow-down",
      hypernym: "arrow-up",
    };
    return icons[type] || "link";
  }

  async loadWordInfo(wordData) {
    const totalRelations =
      (wordData.synonyms?.length || 0) +
      (wordData.antonyms?.length || 0) +
      (wordData.hyponyms?.length || 0) +
      (wordData.hypernyms?.length || 0);

    const avgScore = wordData.avg_score
      ? wordData.avg_score.toFixed(2)
      : "0.00";

    const html = `
            <div class="mb-3">
                <div class="row text-center">
                    <div class="col-6">
                        <div class="h4 text-primary">${totalRelations}</div>
                        <small class="text-muted">Total Relasi</small>
                    </div>
                    <div class="col-6">
                        <div class="h4 text-success">${avgScore}</div>
                        <small class="text-muted">Skor Rata-rata</small>
                    </div>
                </div>
            </div>
            
            <div class="small">
                <div class="mb-2">
                    <strong>Sinonim:</strong> ${wordData.synonyms?.length || 0}
                </div>
                <div class="mb-2">
                    <strong>Antonim:</strong> ${wordData.antonyms?.length || 0}
                </div>
                <div class="mb-2">
                    <strong>Hiponim:</strong> ${wordData.hyponyms?.length || 0}
                </div>
                <div class="mb-2">
                    <strong>Hipernim:</strong> ${
                      wordData.hypernyms?.length || 0
                    }
                </div>
            </div>
        `;

    this.wordInfo.innerHTML = html;
  }

  async loadRelatedWords(wordData) {
    // Get all related words
    const allRelations = [
      ...(wordData.synonyms || []),
      ...(wordData.antonyms || []),
      ...(wordData.hyponyms || []),
      ...(wordData.hypernyms || []),
    ];

    if (allRelations.length === 0) {
      this.relatedWords.innerHTML = `
                <div class="text-center text-muted">
                    <small>Tidak ada kata terkait</small>
                </div>
            `;
      return;
    }

    // Sort by score and take top 5
    const topRelated = allRelations
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 5);

    let html = "";
    topRelated.forEach((relation) => {
      const score = relation.score ? relation.score.toFixed(2) : "0.00";
      html += `
                <div class="mb-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <a href="/thesaurus/word/${encodeURIComponent(
                          relation.word
                        )}" 
                           class="word-link small">${relation.word}</a>
                        <span class="badge bg-secondary small">${score}</span>
                    </div>
                </div>
            `;
    });

    this.relatedWords.innerHTML = html;
  }

  async searchSimilarWords() {
    this.similarWordsModal.show();
    this.similarWordsContent.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Mencari kata serupa...</p>
            </div>
        `;

    try {
      const response = await fetch(
        `/api/public/thesaurus/similar?word=${encodeURIComponent(
          this.word
        )}&limit=10`
      );
      const data = await response.json();

      if (data.success) {
        this.displaySimilarWords(data.data.similar_words || []);
      } else {
        this.similarWordsContent.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-search fa-2x mb-2"></i>
                        <p>${
                          data.message || "Tidak ada kata serupa ditemukan"
                        }</p>
                    </div>
                `;
      }
    } catch (error) {
      console.error("Error searching similar words:", error);
      this.similarWordsContent.innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <p>Terjadi kesalahan saat mencari kata serupa</p>
                </div>
            `;
    }
  }

  displaySimilarWords(similarWords) {
    if (similarWords.length === 0) {
      this.similarWordsContent.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <p>Tidak ada kata serupa ditemukan</p>
                </div>
            `;
      return;
    }

    let html = '<div class="row">';
    similarWords.forEach((word) => {
      const score = word.score ? word.score.toFixed(2) : "0.00";
      html += `
                <div class="col-md-6 mb-2">
                    <div class="card">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <a href="/thesaurus/word/${encodeURIComponent(
                                  word.word
                                )}" 
                                   class="word-link">${word.word}</a>
                                <span class="badge bg-primary">${score}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    });
    html += "</div>";

    this.similarWordsContent.innerHTML = html;
  }

  async exportWordData() {
    try {
      const response = await fetch(
        `/api/public/thesaurus/export/word/${encodeURIComponent(this.word)}`
      );
      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `thesaurus_${this.word}_${
        new Date().toISOString().split("T")[0]
      }.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      this.showAlert("success", "Data berhasil diekspor");
    } catch (error) {
      console.error("Error exporting word data:", error);
      this.showAlert("danger", "Gagal mengekspor data");
    }
  }

  searchWord(word) {
    window.location.href = `/thesaurus/word/${encodeURIComponent(word)}`;
  }

  showWordNotFound() {
    this.wordDetail.innerHTML = `
            <div class="card">
                <div class="card-body text-center">
                    <i class="fas fa-search fa-3x text-muted mb-3"></i>
                    <h5 class="text-muted">Kata tidak ditemukan</h5>
                    <p class="text-muted">Kata "${this.word}" tidak ada dalam tesaurus</p>
                    <a href="/thesaurus" class="btn btn-primary">
                        <i class="fas fa-arrow-left"></i> Kembali ke Tesaurus
                    </a>
                </div>
            </div>
        `;

    this.wordInfo.innerHTML = `
            <div class="text-center text-muted">
                <small>Informasi tidak tersedia</small>
            </div>
        `;

    this.relatedWords.innerHTML = `
            <div class="text-center text-muted">
                <small>Kata terkait tidak tersedia</small>
            </div>
        `;
  }

  showAlert(type, message) {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document
      .querySelector(".container")
      .insertBefore(alertDiv, document.querySelector(".container").firstChild);

    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.detailManager = new ThesaurusDetailManager();
});
