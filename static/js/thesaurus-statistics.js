/**
 * Thesaurus Statistics Manager
 * Handles statistics and charts for thesaurus data
 */
class ThesaurusStatisticsManager {
  constructor() {
    this.totalWords = document.getElementById("totalWords");
    this.totalRelations = document.getElementById("totalRelations");
    this.avgScore = document.getElementById("avgScore");
    this.avgRelations = document.getElementById("avgRelations");
    this.topWordsTable = document.getElementById("topWordsTable");
    this.additionalStats = document.getElementById("additionalStats");

    this.relationChart = null;
    this.topWordsChart = null;

    this.loadStatistics();
  }

  async loadStatistics() {
    try {
      const response = await fetch("/api/public/thesaurus/stats");
      const data = await response.json();

      if (data.success) {
        this.displayBasicStats(data.data);
        this.displayCharts(data.data);
        this.displayTopWordsTable(data.data.top_words || []);
        this.displayAdditionalStats(data.data);
      } else {
        this.showAlert("danger", data.message || "Gagal memuat statistik");
      }
    } catch (error) {
      console.error("Error loading statistics:", error);
      this.showAlert("danger", "Terjadi kesalahan saat memuat statistik");
    }
  }

  displayBasicStats(stats) {
    this.totalWords.textContent = stats.total_words || 0;
    this.totalRelations.textContent = stats.total_relations || 0;
    this.avgScore.textContent = stats.avg_score
      ? stats.avg_score.toFixed(2)
      : "0.00";
    this.avgRelations.textContent = stats.avg_relations_per_word
      ? stats.avg_relations_per_word.toFixed(1)
      : "0.0";
  }

  displayCharts(stats) {
    this.createRelationChart(stats.relation_counts || {});
    this.createTopWordsChart(stats.top_words || []);
  }

  createRelationChart(relationCounts) {
    const ctx = document.getElementById("relationChart");
    if (!ctx) return;

    const labels = ["Sinonim", "Antonim", "Hiponim", "Hipernim"];
    const data = [
      relationCounts.synonym || 0,
      relationCounts.antonym || 0,
      relationCounts.hyponym || 0,
      relationCounts.hypernym || 0,
    ];
    const colors = ["#28a745", "#dc3545", "#ffc107", "#17a2b8"];

    this.relationChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: data,
            backgroundColor: colors,
            borderWidth: 2,
            borderColor: "#fff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 20,
              usePointStyle: true,
            },
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return `${context.label}: ${context.parsed} (${percentage}%)`;
              },
            },
          },
        },
      },
    });
  }

  createTopWordsChart(topWords) {
    const ctx = document.getElementById("topWordsChart");
    if (!ctx) return;

    const labels = topWords.slice(0, 10).map((word) => word.word);
    const data = topWords.slice(0, 10).map((word) => word.relation_count || 0);

    this.topWordsChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Jumlah Relasi",
            data: data,
            backgroundColor: "rgba(102, 126, 234, 0.8)",
            borderColor: "rgba(102, 126, 234, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              title: function (context) {
                return context[0].label;
              },
              label: function (context) {
                return `Relasi: ${context.parsed.y}`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Jumlah Relasi",
            },
          },
          x: {
            title: {
              display: true,
              text: "Kata",
            },
          },
        },
      },
    });
  }

  displayTopWordsTable(topWords) {
    if (topWords.length === 0) {
      this.topWordsTable.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        Tidak ada data kata terpopuler
                    </td>
                </tr>
            `;
      return;
    }

    let html = "";
    const totalRelations = topWords.reduce(
      (sum, word) => sum + (word.relation_count || 0),
      0
    );

    topWords.forEach((word, index) => {
      const relationCount = word.relation_count || 0;
      const percentage =
        totalRelations > 0
          ? ((relationCount / totalRelations) * 100).toFixed(1)
          : "0.0";

      html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>
                        <a href="/thesaurus/word/${encodeURIComponent(
                          word.word
                        )}" 
                           class="word-link">${word.word}</a>
                    </td>
                    <td>
                        <span class="badge bg-primary">${relationCount}</span>
                    </td>
                    <td>
                        <div class="progress progress-custom">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${percentage}%" 
                                 aria-valuenow="${percentage}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                                ${percentage}%
                            </div>
                        </div>
                    </td>
                </tr>
            `;
    });

    this.topWordsTable.innerHTML = html;
  }

  displayAdditionalStats(stats) {
    const html = `
            <div class="mb-3">
                <h6 class="text-primary">
                    <i class="fas fa-chart-line"></i> Distribusi Skor
                </h6>
                <div class="small">
                    <div class="mb-1">
                        <strong>Skor Tertinggi:</strong> ${
                          stats.max_score ? stats.max_score.toFixed(2) : "0.00"
                        }
                    </div>
                    <div class="mb-1">
                        <strong>Skor Terendah:</strong> ${
                          stats.min_score ? stats.min_score.toFixed(2) : "0.00"
                        }
                    </div>
                    <div class="mb-1">
                        <strong>Standar Deviasi:</strong> ${
                          stats.score_std ? stats.score_std.toFixed(2) : "0.00"
                        }
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-success">
                    <i class="fas fa-link"></i> Relasi Terbanyak
                </h6>
                <div class="small">
                    <div class="mb-1">
                        <strong>Maksimal:</strong> ${
                          stats.max_relations || 0
                        } relasi
                    </div>
                    <div class="mb-1">
                        <strong>Minimal:</strong> ${
                          stats.min_relations || 0
                        } relasi
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <h6 class="text-info">
                    <i class="fas fa-calendar"></i> Informasi Dataset
                </h6>
                <div class="small">
                    <div class="mb-1">
                        <strong>Dibuat:</strong> ${
                          stats.created_at
                            ? new Date(stats.created_at).toLocaleDateString(
                                "id-ID"
                              )
                            : "Tidak diketahui"
                        }
                    </div>
                    <div class="mb-1">
                        <strong>Diperbarui:</strong> ${
                          stats.updated_at
                            ? new Date(stats.updated_at).toLocaleDateString(
                                "id-ID"
                              )
                            : "Tidak diketahui"
                        }
                    </div>
                </div>
            </div>
            
            <div class="text-center">
                <button class="btn btn-sm btn-outline-primary" onclick="statsManager.refreshStats()">
                    <i class="fas fa-sync-alt"></i> Perbarui Data
                </button>
            </div>
        `;

    this.additionalStats.innerHTML = html;
  }

  refreshStats() {
    // Destroy existing charts
    if (this.relationChart) {
      this.relationChart.destroy();
      this.relationChart = null;
    }
    if (this.topWordsChart) {
      this.topWordsChart.destroy();
      this.topWordsChart = null;
    }

    // Reload statistics
    this.loadStatistics();
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
  window.statsManager = new ThesaurusStatisticsManager();
});
