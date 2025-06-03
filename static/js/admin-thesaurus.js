/**
 * Thesaurus visualization and search functionality
 */

class ThesaurusManager {
  constructor() {
    // Initialize elements
    this.searchInput = document.getElementById("thesaurusSearchInput");
    this.searchBtn = document.getElementById("thesaurusSearchBtn");
    this.visualizeBtn = document.getElementById("visualizeThesaurusBtn");
    this.visualizationDiv = document.getElementById("thesaurusVisualization");
    this.searchResults = document.getElementById("thesaurusSearchResults");
    this.relationFilters = document.querySelectorAll(".relation-filter"); // Network visualization properties
    this.network = null;
    this.nodes = new vis.DataSet();
    this.edges = new vis.DataSet();

    // Filter states
    this.filters = {
      showSynonyms: true,
      showAntonyms: true,
      showHyponyms: true,
      showHypernyms: true,
    };

    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // Search functionality
    this.searchBtn.addEventListener("click", () => this.searchThesaurus());
    this.searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        this.searchThesaurus();
      }
    });

    // Visualization functionality
    this.visualizeBtn.addEventListener("click", () =>
      this.toggleVisualization()
    );

    // Filter changes
    this.relationFilters.forEach((filter) => {
      filter.addEventListener("change", () => {
        this.updateFilters();
        if (this.network) {
          this.refreshVisualization();
        }
      });
    });
  }

  async searchThesaurus() {
    const searchTerm = this.searchInput.value.trim();
    if (!searchTerm) {
      showAlert("warning", "Masukkan kata yang ingin dicari");
      return;
    }

    try {
      const response = await fetch(
        `/api/thesaurus/search?word=${encodeURIComponent(searchTerm)}`
      );
      const data = await response.json();

      if (data.success) {
        this.displaySearchResults(data.results);
        if (this.visualizationDiv.style.display !== "none") {
          this.visualizeResults(data.results);
        }
      } else {
        showAlert(
          "danger",
          data.message || "Gagal mencari kata dalam tesaurus"
        );
      }
    } catch (error) {
      console.error("Error searching thesaurus:", error);
      showAlert("danger", "Terjadi kesalahan saat mencari kata");
    }
  }

  displaySearchResults(results) {
    const html = this.generateResultsHTML(results);
    this.searchResults.innerHTML = html;
  }

  generateResultsHTML(results) {
    if (!results || Object.keys(results).length === 0) {
      return '<div class="alert alert-info">Tidak ditemukan hasil yang sesuai</div>';
    }

    let html = '<div class="card"><div class="card-body">';

    // Display relations
    const relationTypes = {
      synonyms: { label: "Sinonim", icon: "fa-equals" },
      antonyms: { label: "Antonim", icon: "fa-not-equal" },
      hyponyms: { label: "Hiponim", icon: "fa-level-down-alt" },
      hypernyms: { label: "Hipernim", icon: "fa-level-up-alt" },
    };

    Object.entries(relationTypes).forEach(([type, info]) => {
      if (results[type] && results[type].length > 0) {
        html += `
                    <div class="mb-3">
                        <h6><i class="fas ${info.icon}"></i> ${info.label}:</h6>
                        <div class="d-flex flex-wrap gap-1">
                            ${results[type]
                              .map(
                                (word) =>
                                  `<span class="badge bg-secondary px-2 py-1" 
                                       style="cursor: pointer" 
                                       onclick="thesaurusManager.searchWord('${word}')">${word}</span>`
                              )
                              .join("")}
                        </div>
                    </div>`;
      }
    });

    html += "</div></div>";
    return html;
  }

  searchWord(word) {
    this.searchInput.value = word;
    this.searchThesaurus();
  }

  toggleVisualization() {
    if (this.visualizationDiv.style.display === "none") {
      this.visualizationDiv.style.display = "block";
      if (this.searchInput.value) {
        this.searchThesaurus();
      }
    } else {
      this.visualizationDiv.style.display = "none";
      if (this.network) {
        this.network.destroy();
        this.network = null;
      }
    }
  }

  visualizeResults(results) {
    // Clear existing network
    if (this.network) {
      this.network.destroy();
    }

    // Create nodes and edges from results
    const { nodes, edges } = this.createGraphData(results);

    // Create network
    const container = this.visualizationDiv;
    const data = { nodes, edges };
    const options = {
      nodes: {
        shape: "box",
        margin: 10,
        font: { size: 14 },
      },
      edges: {
        arrows: "to",
        color: {
          inherit: "both",
        },
      },
      physics: {
        stabilization: true,
        barnesHut: {
          gravitationalConstant: -2000,
          springConstant: 0.04,
        },
      },
    };

    this.network = new vis.Network(container, data, options);
  }

  createGraphData(results) {
    const nodes = new vis.DataSet();
    const edges = new vis.DataSet();
    const searchWord = this.searchInput.value.trim();

    // Add central node
    nodes.add({
      id: searchWord,
      label: searchWord,
      color: "#e04141",
    });

    // Add relations based on filters
    const relationColors = {
      synonyms: { color: "#4CAF50", label: "sinonim" },
      antonyms: { color: "#f44336", label: "antonim" },
      hyponyms: { color: "#2196F3", label: "hiponim" },
      hypernyms: { color: "#9C27B0", label: "hipernim" },
    };

    Object.entries(results).forEach(([relationType, words]) => {
      if (
        this.filters[
          `show${relationType.charAt(0).toUpperCase() + relationType.slice(1)}`
        ]
      ) {
        words.forEach((word) => {
          if (!nodes.get(word)) {
            nodes.add({
              id: word,
              label: word,
              color: "#666",
            });
          }

          edges.add({
            from: searchWord,
            to: word,
            color: relationColors[relationType].color,
            label: relationColors[relationType].label,
          });
        });
      }
    });

    return { nodes, edges };
  }

  updateFilters() {
    this.filters = {
      showSynonyms: document.getElementById("showSynonyms").checked,
      showAntonyms: document.getElementById("showAntonyms").checked,
      showHyponyms: document.getElementById("showHyponyms").checked,
      showHypernyms: document.getElementById("showHypernyms").checked,
    };
  }

  refreshVisualization() {
    if (this.network && this.searchInput.value) {
      this.searchThesaurus();
    }
  }
}

// Initialize when document is ready
document.addEventListener("DOMContentLoaded", () => {
  window.thesaurusManager = new ThesaurusManager();
});
