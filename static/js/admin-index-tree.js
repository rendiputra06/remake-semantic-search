/**
 * Index tree management functionality for admin panel
 */

function loadIndexTree() {
  const treeContainer = document.getElementById("index-tree-container");
  const treeLoading = document.getElementById("index-tree-loading");

  fetch("/api/quran-index/tree")
    .then((response) => response.json())
    .then((result) => {
      if (result.success) {
        treeContainer.innerHTML = buildTreeHtml(result.data);

        // Initialize event listeners for expand/collapse
        const togglers = document.querySelectorAll(".index-tree-toggler");
        togglers.forEach((toggler) => {
          toggler.addEventListener("click", function () {
            const childContainer = this.nextElementSibling;
            childContainer.classList.toggle("d-none");
            this.querySelector("i").classList.toggle("fa-caret-right");
            this.querySelector("i").classList.toggle("fa-caret-down");
          });
        });
      } else {
        showAlert("danger", "Gagal memuat struktur indeks");
        treeContainer.innerHTML =
          '<div class="alert alert-warning">Tidak dapat memuat struktur indeks.</div>';
      }
    })
    .catch((error) => {
      console.error("Error loading index tree:", error);
      showAlert("danger", "Terjadi kesalahan saat memuat struktur indeks");
      treeContainer.innerHTML =
        '<div class="alert alert-danger">Error: ' + error.message + "</div>";
    })
    .finally(() => {
      // Hide loading spinner
      treeLoading.classList.add("d-none");
    });
}

function buildTreeHtml(data, level = 0) {
  if (!data || !data.length) return "";

  let html =
    '<ul class="index-tree list-unstyled ms-' + (level > 0 ? "4" : "0") + '">';

  data.forEach((item) => {
    const hasChildren =
      item.has_children && item.children && item.children.length > 0;
    const ayatHtml = displayAyatList(item.list_ayat);

    html += '<li class="index-tree-item mb-2">';

    if (hasChildren) {
      html += `<div class="index-tree-toggler" style="cursor:pointer">
                        <i class="fas fa-caret-right me-1"></i>
                        <strong>${item.title}</strong> 
                        <span class="text-muted">(Level ${item.level})</span>
                        ${ayatHtml}
                     </div>
                     <div class="index-tree-children d-none">
                        ${buildTreeHtml(item.children, level + 1)}
                     </div>`;
    } else {
      html += `<div class="ms-3">
                        <strong>${item.title}</strong> 
                        <span class="text-muted">(Level ${item.level})</span>
                        ${ayatHtml}
                     </div>`;
    }

    html += "</li>";
  });

  html += "</ul>";
  return html;
}

function displayAyatList(jsonString) {
  if (!jsonString) return "";

  try {
    const ayatList = JSON.parse(jsonString);
    if (!ayatList || !ayatList.length) return "";

    let html = '<div class="mt-1"><strong>Ayat:</strong> ';
    ayatList.forEach((ayat, index) => {
      html += `<span class="badge bg-info me-1">${ayat}</span>`;
    });
    html += "</div>";

    return html;
  } catch (e) {
    console.error("Error parsing ayat JSON:", e);
    return "";
  }
}

// Add event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Event listener untuk tab index Al-Quran
  const quranIndexTab = document.getElementById("quran-index-tab");
  if (quranIndexTab) {
    quranIndexTab.addEventListener("shown.bs.tab", function () {
      const treeContainer = document.getElementById("index-tree-container");
      const treeLoading = document.getElementById("index-tree-loading");

      // Load only if not loaded before or needs refresh
      if (treeContainer.children.length === 0) {
        treeContainer.innerHTML = "";
        treeLoading.classList.remove("d-none");
        loadIndexTree();
      }
    });
  }
});
