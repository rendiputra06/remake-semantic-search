// ===== ADMIN ONTOLOGY JS =====
// Semua kode JS dari ontology_admin.html dipindahkan ke sini.
// Siapkan struktur modular agar mudah dikembangkan (autocomplete, validasi, dsb).

// Variabel global
let concepts = [];
let editMode = false;
let filteredConcepts = [];
let currentPage = 1;
const pageSize = 10;
let deleteConceptId = null;

// Global variable untuk menyimpan filter state
let visualizationFilters = {
  broader: true,
  narrower: true,
  related: true,
};

// Global variables untuk audit trail
let auditLogs = [];
let auditStats = {};
let auditCurrentPage = 1;
let auditPageSize = 20;
let auditFilters = {
  concept_id: "",
  action: "",
  username: "",
};

// Toast notification
function showToast(msg, type = "success") {
  const container = document.getElementById("admin-toast-container");
  const id = "toast-" + Date.now();
  const color =
    type === "success"
      ? "bg-success"
      : type === "danger"
      ? "bg-danger"
      : "bg-warning";
  const html = `<div id="${id}" class="toast align-items-center text-white ${color} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
    <div class="d-flex">
      <div class="toast-body">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  </div>`;
  container.insertAdjacentHTML("beforeend", html);
  const toastEl = document.getElementById(id);
  const toast = new bootstrap.Toast(toastEl);
  toast.show();
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

function showLoading(show) {
  document.getElementById("loading-spinner").style.display = show ? "" : "none";
}

function filterAndPaginateConcepts() {
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  filteredConcepts = concepts.filter(
    (c) =>
      c.label.toLowerCase().includes(q) ||
      (c.synonyms || []).some((s) => s.toLowerCase().includes(q))
  );
  currentPage = 1;
  renderTable();
  renderPagination();
}

function renderTable() {
  const tbody = document.querySelector("#ontology-table tbody");
  tbody.innerHTML = "";
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  const pageData = (
    filteredConcepts.length ? filteredConcepts : concepts
  ).slice(start, end);
  pageData.forEach((c) => {
    tbody.innerHTML += `<tr>
      <td>${c.id}</td>
      <td>${c.label}</td>
      <td>${(c.synonyms || [])
        .map((s) => `<span class='badge bg-info me-1'>${s}</span>`)
        .join("")}</td>
      <td>${(c.broader || [])
        .map((s) => `<span class='badge bg-secondary me-1'>${s}</span>`)
        .join("")}</td>
      <td>${(c.narrower || [])
        .map((s) => `<span class='badge bg-secondary me-1'>${s}</span>`)
        .join("")}</td>
      <td>${(c.related || [])
        .map((s) => `<span class='badge bg-warning text-dark me-1'>${s}</span>`)
        .join("")}</td>
      <td>${(c.verses || [])
        .map((s) => `<span class='badge bg-success me-1'>${s}</span>`)
        .join("")}</td>
      <td>
        <button class='btn btn-sm btn-info me-1' onclick='showEditModal("${
          c.id
        }")'><i class='fas fa-edit'></i></button>
        <button class='btn btn-sm btn-danger' onclick='showDeleteModal("${
          c.id
        }")'><i class='fas fa-trash'></i></button>
      </td>
    </tr>`;
  });
}

function renderPagination() {
  const total = (filteredConcepts.length ? filteredConcepts : concepts).length;
  const totalPages = Math.ceil(total / pageSize);
  let html = "";
  if (totalPages > 1) {
    html += `<nav><ul class="pagination justify-content-end mb-0">`;
    for (let i = 1; i <= totalPages; i++) {
      html += `<li class="page-item${
        i === currentPage ? " active" : ""
      }"><a class="page-link" href="#" onclick="gotoPage(${i});return false;">${i}</a></li>`;
    }
    html += `</ul></nav>`;
  }
  document.getElementById("pagination-controls").innerHTML = html;
}

function gotoPage(page) {
  currentPage = page;
  renderTable();
  renderPagination();
}

function loadConcepts() {
  showLoading(true);
  fetch("/api/ontology/admin/all")
    .then((res) => res.json())
    .then((data) => {
      showLoading(false);
      if (!data.success) {
        showToast(data.message, "danger");
        return;
      }
      concepts = data.concepts;
      filteredConcepts = [];
      renderTable();
      renderPagination();
      renderNetwork();
    })
    .catch(() => showLoading(false));
}

function showAddModal() {
  editMode = false;
  document.getElementById("conceptModalLabel").textContent = "Tambah Konsep";
  document.getElementById("conceptForm").reset();
  document.getElementById("concept-id").disabled = false;
  document.getElementById("concept-id-old").value = "";
  new bootstrap.Modal(document.getElementById("conceptModal")).show();
}

function showEditModal(id) {
  editMode = true;
  const c = concepts.find((x) => x.id === id);
  if (!c) return;
  document.getElementById("conceptModalLabel").textContent = "Edit Konsep";
  document.getElementById("concept-id").value = c.id;
  document.getElementById("concept-id").disabled = true;
  document.getElementById("concept-id-old").value = c.id;
  document.getElementById("concept-label").value = c.label;
  document.getElementById("concept-synonyms").value = (c.synonyms || []).join(
    ", "
  );
  document.getElementById("concept-broader").value = (c.broader || []).join(
    ", "
  );
  document.getElementById("concept-narrower").value = (c.narrower || []).join(
    ", "
  );
  document.getElementById("concept-related").value = (c.related || []).join(
    ", "
  );
  document.getElementById("concept-verses").value = (c.verses || []).join(", ");
  new bootstrap.Modal(document.getElementById("conceptModal")).show();
}

function showDeleteModal(id) {
  const c = concepts.find((x) => x.id === id);
  if (!c) return;
  deleteConceptId = id;
  document.getElementById("delete-label").textContent =
    c.label + " (" + c.id + ")";
  new bootstrap.Modal(document.getElementById("deleteConfirmModal")).show();
}

document.getElementById("confirm-delete-btn").onclick = function () {
  if (!deleteConceptId) return;
  showLoading(true);
  fetch(`/api/ontology/admin/delete/${deleteConceptId}`, { method: "DELETE" })
    .then((res) => res.json())
    .then((res) => {
      showLoading(false);
      if (res.success) {
        showToast("Konsep berhasil dihapus.", "success");
        loadConcepts();
      } else {
        showToast(res.message, "danger");
      }
    })
    .catch(() => showLoading(false));
};

function showAlert(msg, type = "success") {
  showToast(msg, type);
}

function submitImport() {
  const fileInput = document.getElementById("importFile");
  if (!fileInput.files.length) {
    showToast("Pilih file terlebih dahulu.", "warning");
    return;
  }
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  showLoading(true);
  fetch("/api/ontology/admin/import", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((res) => {
      showLoading(false);
      if (res.success) {
        showToast("Import berhasil: " + (res.message || ""), "success");
        loadConcepts();
        bootstrap.Modal.getInstance(
          document.getElementById("importModal")
        ).hide();
      } else {
        showToast(
          "Import gagal: " + (res.message || "Format tidak valid"),
          "danger"
        );
      }
    })
    .catch(() => {
      showLoading(false);
      showToast("Terjadi error saat import.", "danger");
    });
}

function exportConcepts() {
  showLoading(true);
  // Export data sesuai filter/pagination (default: semua data yang sedang ditampilkan)
  const data = filteredConcepts.length ? filteredConcepts : concepts;
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ontology_export.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showLoading(false);
  showToast("Export berhasil.", "success");
}

// ========== CRUD LANJUTAN ========== //
// Autocomplete untuk field relasi (broader, narrower, related)
function setupAutocomplete() {
  const allIds = concepts.map((c) => c.id);
  ["concept-broader", "concept-narrower", "concept-related"].forEach(
    (fieldId) => {
      const input = document.getElementById(fieldId);
      if (!input) return;
      // Buat datalist
      let datalistId = fieldId + "-list";
      let datalist = document.getElementById(datalistId);
      if (!datalist) {
        datalist = document.createElement("datalist");
        datalist.id = datalistId;
        document.body.appendChild(datalist);
        input.setAttribute("list", datalistId);
      }
      datalist.innerHTML = allIds
        .map((id) => `<option value="${id}">`)
        .join("");
    }
  );
}

// Validasi real-time relasi (ID tidak ditemukan)
function validateRelasiField(fieldId) {
  const input = document.getElementById(fieldId);
  const errorId = fieldId + "-error";
  let error = document.getElementById(errorId);
  if (!error) {
    error = document.createElement("div");
    error.id = errorId;
    error.className = "text-danger small mt-1";
    input.parentNode.appendChild(error);
  }
  const ids = input.value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const allIds = concepts.map((c) => c.id);
  const notFound = ids.filter((id) => id && !allIds.includes(id));
  if (notFound.length) {
    error.textContent = "ID tidak ditemukan: " + notFound.join(", ");
    input.classList.add("is-invalid");
  } else {
    error.textContent = "";
    input.classList.remove("is-invalid");
  }
}

// Validasi duplikasi ID sebelum simpan
function validateDuplicateId() {
  const idInput = document.getElementById("concept-id");
  const errorId = "concept-id-error";
  let error = document.getElementById(errorId);
  if (!error) {
    error = document.createElement("div");
    error.id = errorId;
    error.className = "text-danger small mt-1";
    idInput.parentNode.appendChild(error);
  }
  const id = idInput.value.trim();
  const exists = concepts.some((c) => c.id === id);
  if (exists && !editMode) {
    error.textContent = "ID sudah ada, gunakan ID lain.";
    idInput.classList.add("is-invalid");
    return false;
  } else {
    error.textContent = "";
    idInput.classList.remove("is-invalid");
    return true;
  }
}

// UX form: tombol reset
function setupFormUX() {
  const form = document.getElementById("conceptForm");
  if (!form) return;
  let resetBtn = document.getElementById("concept-form-reset");
  if (!resetBtn) {
    resetBtn = document.createElement("button");
    resetBtn.type = "reset";
    resetBtn.className = "btn btn-secondary btn-sm ms-2";
    resetBtn.id = "concept-form-reset";
    resetBtn.textContent = "Reset";
    form.querySelector(".mb-3:last-child").appendChild(resetBtn);
  }
}

// Integrasi validasi ke event form
function setupFormValidation() {
  ["concept-broader", "concept-narrower", "concept-related"].forEach(
    (fieldId) => {
      const input = document.getElementById(fieldId);
      if (input) {
        input.addEventListener("input", () => validateRelasiField(fieldId));
      }
    }
  );
  const idInput = document.getElementById("concept-id");
  if (idInput) {
    idInput.addEventListener("input", validateDuplicateId);
  }
}

// Override save concept untuk validasi sebelum submit
const oldSaveBtn = document.getElementById("save-concept-btn");
if (oldSaveBtn) {
  oldSaveBtn.onclick = function () {
    if (!validateDuplicateId()) {
      showToast("Perbaiki error pada form sebelum menyimpan.", "danger");
      return;
    }
    // Validasi relasi
    let relasiValid = true;
    ["concept-broader", "concept-narrower", "concept-related"].forEach(
      (fieldId) => {
        validateRelasiField(fieldId);
        const input = document.getElementById(fieldId);
        if (input && input.classList.contains("is-invalid"))
          relasiValid = false;
      }
    );
    if (!relasiValid) {
      showToast("Perbaiki error pada field relasi.", "danger");
      return;
    }
    // Lanjutkan proses simpan (panggil fungsi simpan asli)
    // ... (kode simpan asli, bisa diintegrasikan di sini)
  };
}

function loadStorageInfo() {
  fetch("/api/ontology/admin/storage/info")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        const info = data.info;
        document.getElementById("storage-type").textContent = info.storage_type;
        document.getElementById("concept-count").textContent =
          info.concept_count;
        document.getElementById("json-path").textContent =
          info.json_path || "N/A";

        // Update button states
        const dbBtn = document.querySelector(
          "button[onclick=\"switchStorage('database')\"]"
        );
        const jsonBtn = document.querySelector(
          "button[onclick=\"switchStorage('json')\"]"
        );

        if (info.storage_type === "database") {
          dbBtn.classList.remove("btn-outline-primary");
          dbBtn.classList.add("btn-primary");
          jsonBtn.classList.remove("btn-secondary");
          jsonBtn.classList.add("btn-outline-secondary");
        } else {
          jsonBtn.classList.remove("btn-outline-secondary");
          jsonBtn.classList.add("btn-secondary");
          dbBtn.classList.remove("btn-primary");
          dbBtn.classList.add("btn-outline-primary");
        }
      }
    })
    .catch((err) => {
      console.error("Error loading storage info:", err);
      document.getElementById("storage-type").textContent = "Error";
      document.getElementById("concept-count").textContent = "Error";
      document.getElementById("json-path").textContent = "Error";
    });
}

function switchStorage(storageType) {
  if (!confirm(`Yakin ingin switch ke ${storageType} storage?`)) return;

  fetch("/api/ontology/admin/storage/switch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ storage_type: storageType }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showToast(data.message);
        loadStorageInfo();
        loadConcepts(); // Reload concepts after switch
      } else {
        showToast(data.message, "danger");
      }
    })
    .catch((err) => {
      showToast("Error switching storage: " + err.message, "danger");
    });
}

function syncStorage(direction) {
  const directionText =
    direction === "json_to_db" ? "JSON ke Database" : "Database ke JSON";
  if (!confirm(`Yakin ingin sync ${directionText}?`)) return;

  fetch("/api/ontology/admin/storage/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ direction: direction }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showToast(data.message);
        loadStorageInfo();
        if (direction === "json_to_db") {
          loadConcepts(); // Reload concepts after sync
        }
      } else {
        showToast(data.message, "danger");
      }
    })
    .catch((err) => {
      showToast("Error syncing storage: " + err.message, "danger");
    });
}

document.addEventListener("DOMContentLoaded", function () {
  loadStorageInfo();
  loadConcepts();
  document
    .getElementById("searchInput")
    .addEventListener("input", filterAndPaginateConcepts);
  setupAutocomplete();
  setupFormUX();
  setupFormValidation();

  // Setup tab event listeners
  setupTabListeners();
});

function setupTabListeners() {
  // Audit tab listener
  const auditTab = document.getElementById("audit-tab");
  if (auditTab) {
    auditTab.addEventListener("shown.bs.tab", function (e) {
      // Load audit data when audit tab is shown
      loadAuditStats();
      loadAuditLog();
    });
  }

  // Visualization tab listener
  const visualizationTab = document.getElementById("visualization-tab");
  if (visualizationTab) {
    visualizationTab.addEventListener("shown.bs.tab", function (e) {
      // Re-render visualization when tab is shown
      if (concepts && concepts.length > 0) {
        renderNetwork();
      }
    });
  }
}

function renderNetwork() {
  const container = document.getElementById("ontology-network");
  if (!container || !concepts || !concepts.length) {
    console.log("Container tidak ditemukan atau tidak ada data konsep");
    return;
  }

  // Use bubble net as default visualization
  switchVisualization("bubble");
}

// Function to apply visualization filters
function applyVisualizationFilters() {
  // Update filter state
  visualizationFilters = {
    broader: document.getElementById("filter-broader").checked,
    narrower: document.getElementById("filter-narrower").checked,
    related: document.getElementById("filter-related").checked,
  };

  // Re-render current visualization with filters
  const container = document.getElementById("ontology-network");
  if (!container || !concepts || !concepts.length) return;

  // Determine current visualization type
  let currentType = "bubble";
  const activeButton = document.querySelector(
    ".btn-group .btn:not(.btn-outline-primary):not(.btn-outline-secondary):not(.btn-outline-info)"
  );
  if (activeButton) {
    const onclick = activeButton.getAttribute("onclick");
    if (onclick.includes("bubble")) currentType = "bubble";
    else if (onclick.includes("hierarchical")) currentType = "hierarchical";
    else if (onclick.includes("force")) currentType = "force";
  }

  // Re-render with current type and filters
  switchVisualization(currentType);

  // Show filter summary
  const activeFilters = Object.entries(visualizationFilters)
    .filter(([key, value]) => value)
    .map(([key]) => key)
    .join(", ");

  showToast(`Filter diterapkan: ${activeFilters || "Semua relasi"}`, "success");
}

function createOntologyGraphData(concepts) {
  const nodes = [];
  const edges = [];
  const nodeMap = new Map();

  // Create nodes for each concept
  concepts.forEach((concept, index) => {
    // Calculate node size based on number of relations
    const relationCount =
      (concept.synonyms?.length || 0) +
      (concept.broader?.length || 0) +
      (concept.narrower?.length || 0) +
      (concept.related?.length || 0);
    const nodeSize = Math.max(20, Math.min(35, 20 + relationCount * 2));

    // Determine node color based on concept type
    let nodeColor = "#007bff"; // Default blue
    if (concept.broader && concept.broader.length > 0) {
      nodeColor = "#28a745"; // Green for broader concepts
    } else if (concept.narrower && concept.narrower.length > 0) {
      nodeColor = "#ffc107"; // Yellow for narrower concepts
    } else if (concept.related && concept.related.length > 0) {
      nodeColor = "#dc3545"; // Red for related concepts
    }

    const node = {
      id: concept.id,
      label: concept.label,
      size: nodeSize,
      color: {
        background: nodeColor,
        border: "#ffffff",
        highlight: {
          background: nodeColor,
          border: "#ffffff",
        },
      },
      font: {
        size: Math.max(10, Math.min(16, 10 + relationCount)),
        color: "#ffffff",
        face: "Arial",
      },
      title: createNodeTooltip(concept),
      conceptId: concept.id,
    };

    nodes.push(node);
    nodeMap.set(concept.id, node);
  });

  // Create edges for relationships based on filters
  concepts.forEach((concept) => {
    // Broader relationships
    if (concept.broader && visualizationFilters.broader) {
      concept.broader.forEach((broaderId) => {
        if (nodeMap.has(broaderId)) {
          edges.push({
            from: concept.id,
            to: broaderId,
            color: {
              color: "#28a745",
              highlight: "#28a745",
              opacity: 0.8,
            },
            width: 3,
            label: "broader",
            font: {
              size: 10,
              color: "#28a745",
            },
            arrows: {
              to: {
                enabled: true,
                scaleFactor: 0.6,
              },
            },
          });
        }
      });
    }

    // Narrower relationships
    if (concept.narrower && visualizationFilters.narrower) {
      concept.narrower.forEach((narrowerId) => {
        if (nodeMap.has(narrowerId)) {
          edges.push({
            from: concept.id,
            to: narrowerId,
            color: {
              color: "#ffc107",
              highlight: "#ffc107",
              opacity: 0.8,
            },
            width: 2,
            label: "narrower",
            font: {
              size: 10,
              color: "#ffc107",
            },
            arrows: {
              to: {
                enabled: true,
                scaleFactor: 0.6,
              },
            },
          });
        }
      });
    }

    // Related relationships
    if (concept.related && visualizationFilters.related) {
      concept.related.forEach((relatedId) => {
        if (nodeMap.has(relatedId)) {
          edges.push({
            from: concept.id,
            to: relatedId,
            color: {
              color: "#dc3545",
              highlight: "#dc3545",
              opacity: 0.6,
            },
            width: 1,
            label: "related",
            font: {
              size: 10,
              color: "#dc3545",
            },
            arrows: {
              to: {
                enabled: false,
              },
            },
            dashes: true,
          });
        }
      });
    }
  });

  return { nodes, edges };
}

function createNodeTooltip(concept) {
  let tooltip = `<div style="text-align: left; max-width: 300px;">
    <strong>${concept.label}</strong> (${concept.id})<br><br>`;

  if (concept.synonyms && concept.synonyms.length > 0) {
    tooltip += `<strong>Sinonim:</strong> ${concept.synonyms.join(", ")}<br>`;
  }

  if (concept.broader && concept.broader.length > 0) {
    tooltip += `<strong>Broader:</strong> ${concept.broader.join(", ")}<br>`;
  }

  if (concept.narrower && concept.narrower.length > 0) {
    tooltip += `<strong>Narrower:</strong> ${concept.narrower.join(", ")}<br>`;
  }

  if (concept.related && concept.related.length > 0) {
    tooltip += `<strong>Related:</strong> ${concept.related.join(", ")}<br>`;
  }

  if (concept.verses && concept.verses.length > 0) {
    tooltip += `<strong>Ayat:</strong> ${concept.verses.join(", ")}<br>`;
  }

  tooltip += "</div>";
  return tooltip;
}

// Function to update visualization statistics
function updateVisualizationStats(nodes, edges) {
  const nodeCountElement = document.getElementById("node-count");
  const edgeCountElement = document.getElementById("edge-count");

  if (nodeCountElement) {
    nodeCountElement.textContent = nodes.length;
  }

  if (edgeCountElement) {
    edgeCountElement.textContent = edges.length;
  }
}

// Function to switch visualization type
function switchVisualization(type) {
  const container = document.getElementById("ontology-network");
  if (!container || !concepts || !concepts.length) return;

  // Clear existing network
  if (window.ontologyNetwork) {
    window.ontologyNetwork.destroy();
  }

  // Update button states
  updateVisualizationButtons(type);

  let data, options;

  switch (type) {
    case "bubble":
      // Bubble net visualization (default)
      const bubbleData = createOntologyGraphData(concepts);
      data = {
        nodes: new vis.DataSet(bubbleData.nodes),
        edges: new vis.DataSet(bubbleData.edges),
      };
      options = {
        nodes: {
          shape: "circle",
          borderWidth: 2,
          shadow: true,
          font: { size: 12, color: "#ffffff" },
          scaling: { min: 15, max: 35 },
        },
        edges: {
          width: 2,
          shadow: true,
          smooth: { type: "curvedCW", roundness: 0.2 },
        },
        physics: {
          barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            springLength: 100,
            springConstant: 0.04,
          },
        },
      };
      break;

    case "hierarchical":
      // Hierarchical tree visualization
      const treeData = createHierarchicalData(concepts);
      data = {
        nodes: new vis.DataSet(treeData.nodes),
        edges: new vis.DataSet(treeData.edges),
      };
      options = {
        nodes: {
          shape: "box",
          margin: 10,
          font: { size: 14 },
        },
        edges: {
          width: 2,
          smooth: { type: "cubicBezier" },
        },
        layout: {
          hierarchical: {
            enabled: true,
            direction: "UD",
            sortMethod: "directed",
          },
        },
        physics: false,
      };
      break;

    case "force":
      // Force-directed graph
      const forceData = createOntologyGraphData(concepts);
      data = {
        nodes: new vis.DataSet(forceData.nodes),
        edges: new vis.DataSet(forceData.edges),
      };
      options = {
        nodes: {
          shape: "dot",
          size: 20,
          font: { size: 12 },
        },
        edges: {
          width: 1,
          smooth: { type: "continuous" },
        },
        physics: {
          forceAtlas2Based: {
            gravitationalConstant: -50,
            centralGravity: 0.01,
            springLength: 100,
            springConstant: 0.08,
          },
        },
      };
      break;

    default:
      return;
  }

  window.ontologyNetwork = new vis.Network(container, data, options);

  // Update statistics
  updateVisualizationStats(data.nodes.get(), data.edges.get());

  // Add event listeners
  window.ontologyNetwork.on("click", function (params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const node = data.nodes.get(nodeId);
      if (node && node.conceptId) {
        showEditModal(node.conceptId);
      }
    }
  });

  // Add hover effects
  window.ontologyNetwork.on("hoverNode", function (params) {
    const connectedNodes = window.ontologyNetwork.getConnectedNodes(
      params.node
    );
    window.ontologyNetwork.selectNodes([params.node, ...connectedNodes]);
  });

  window.ontologyNetwork.on("blurNode", function (params) {
    window.ontologyNetwork.unselectAll();
  });

  showToast(`Berhasil beralih ke visualisasi ${type}`, "success");
}

function updateVisualizationButtons(activeType) {
  // Reset all buttons
  const buttons = document.querySelectorAll('[onclick^="switchVisualization"]');
  buttons.forEach((btn) => {
    btn.classList.remove("btn-primary", "btn-secondary", "btn-info");
    btn.classList.add(
      "btn-outline-primary",
      "btn-outline-secondary",
      "btn-outline-info"
    );
  });

  // Activate selected button
  const activeButton = document.querySelector(
    `[onclick="switchVisualization('${activeType}')"]`
  );
  if (activeButton) {
    activeButton.classList.remove(
      "btn-outline-primary",
      "btn-outline-secondary",
      "btn-outline-info"
    );
    switch (activeType) {
      case "bubble":
        activeButton.classList.add("btn-primary");
        break;
      case "hierarchical":
        activeButton.classList.add("btn-secondary");
        break;
      case "force":
        activeButton.classList.add("btn-info");
        break;
    }
  }
}

function createHierarchicalData(concepts) {
  const nodes = [];
  const edges = [];
  const nodeMap = new Map();

  // Create nodes
  concepts.forEach((concept) => {
    const node = {
      id: concept.id,
      label: concept.label,
      title: createNodeTooltip(concept),
      conceptId: concept.id,
    };
    nodes.push(node);
    nodeMap.set(concept.id, node);
  });

  // Create hierarchical edges based on filters
  concepts.forEach((concept) => {
    // Broader relationships (parent -> child)
    if (concept.broader && visualizationFilters.broader) {
      concept.broader.forEach((broaderId) => {
        if (nodeMap.has(broaderId)) {
          edges.push({
            from: broaderId,
            to: concept.id,
            color: "#28a745",
            width: 2,
            label: "broader",
          });
        }
      });
    }

    // Narrower relationships (child -> parent, but we'll show as parent -> child for hierarchy)
    if (concept.narrower && visualizationFilters.narrower) {
      concept.narrower.forEach((narrowerId) => {
        if (nodeMap.has(narrowerId)) {
          edges.push({
            from: concept.id,
            to: narrowerId,
            color: "#ffc107",
            width: 2,
            label: "narrower",
          });
        }
      });
    }

    // Related relationships (bidirectional, shown as dashed)
    if (concept.related && visualizationFilters.related) {
      concept.related.forEach((relatedId) => {
        if (nodeMap.has(relatedId)) {
          edges.push({
            from: concept.id,
            to: relatedId,
            color: "#dc3545",
            width: 1,
            label: "related",
            dashes: true,
          });
        }
      });
    }
  });

  return { nodes, edges };
}

// Function to export visualization as image
function exportVisualization() {
  if (!window.ontologyNetwork) {
    showToast("Tidak ada visualisasi yang aktif", "warning");
    return;
  }

  try {
    // Get canvas data
    const canvas = window.ontologyNetwork.canvas.frame.canvas;
    const dataURL = canvas.toDataURL("image/png");

    // Create download link
    const link = document.createElement("a");
    link.download = `ontology_visualization_${new Date()
      .toISOString()
      .slice(0, 10)}.png`;
    link.href = dataURL;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast("Visualisasi berhasil diekspor", "success");
  } catch (error) {
    console.error("Error exporting visualization:", error);
    showToast("Gagal mengekspor visualisasi", "danger");
  }
}

// ========== AUDIT TRAIL FUNCTIONS ========== //

function loadAuditStats() {
  fetch("/api/ontology/admin/audit/stats")
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        auditStats = data.stats;
        updateAuditStatsDisplay();
      }
    })
    .catch((err) => {
      console.error("Error loading audit stats:", err);
    });
}

function updateAuditStatsDisplay() {
  document.getElementById("audit-total").textContent =
    auditStats.total_entries || 0;
  document.getElementById("audit-recent").textContent =
    auditStats.recent_activity || 0;
  document.getElementById("audit-users").textContent =
    auditStats.top_users?.length || 0;
  document.getElementById("audit-actions").textContent = Object.keys(
    auditStats.action_counts || {}
  ).length;
}

function loadAuditLog(page = 1) {
  auditCurrentPage = page;

  // Update filters from UI
  auditFilters.concept_id = document
    .getElementById("audit-search")
    .value.trim();
  auditFilters.action = document.getElementById("audit-action-filter").value;
  auditFilters.username = document.getElementById("audit-user-filter").value;

  // Build query parameters
  const params = new URLSearchParams({
    limit: auditPageSize,
    offset: (page - 1) * auditPageSize,
  });

  if (auditFilters.concept_id) {
    params.append("concept_id", auditFilters.concept_id);
  }
  if (auditFilters.action) {
    params.append("action", auditFilters.action);
  }

  fetch(`/api/ontology/admin/audit/log?${params}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        auditLogs = data.audit_logs;
        renderAuditTable();
        renderAuditPagination();
        updateAuditUserFilter();
      } else {
        showToast(data.message || "Gagal memuat audit log", "danger");
      }
    })
    .catch((err) => {
      console.error("Error loading audit log:", err);
      showToast("Error memuat audit log", "danger");
    });
}

function renderAuditTable() {
  const tbody = document.getElementById("audit-tbody");
  tbody.innerHTML = "";

  if (!auditLogs.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted">
          <i class="fas fa-info-circle me-2"></i>Tidak ada data audit log
        </td>
      </tr>
    `;
    return;
  }

  auditLogs.forEach((log) => {
    const actionBadge = getActionBadge(log.action);
    const changesText = log.changes || "Tidak ada perubahan";
    const timestamp = new Date(log.timestamp).toLocaleString("id-ID");

    tbody.innerHTML += `
      <tr>
        <td>
          <small class="text-muted">${timestamp}</small>
        </td>
        <td>
          <span class="badge bg-secondary">${log.username || "Unknown"}</span>
        </td>
        <td>${actionBadge}</td>
        <td>
          <code>${log.concept_id}</code>
        </td>
        <td>
          <small class="text-muted">${changesText}</small>
        </td>
        <td>
          <small class="text-muted">${log.ip_address || "N/A"}</small>
        </td>
        <td>
          <button class="btn btn-sm btn-outline-info" onclick="showAuditDetail('${
            log.id
          }')" title="Lihat detail">
            <i class="fas fa-eye"></i>
          </button>
        </td>
      </tr>
    `;
  });
}

function getActionBadge(action) {
  const badges = {
    CREATE: '<span class="badge bg-success">Create</span>',
    UPDATE: '<span class="badge bg-warning text-dark">Update</span>',
    DELETE: '<span class="badge bg-danger">Delete</span>',
  };
  return badges[action] || `<span class="badge bg-secondary">${action}</span>`;
}

function renderAuditPagination() {
  const pagination = document.getElementById("audit-pagination");
  pagination.innerHTML = "";

  // Simple pagination - in real app, you'd get total count from API
  const totalPages = Math.ceil(auditLogs.length / auditPageSize);

  if (totalPages <= 1) return;

  // Previous button
  const prevLi = document.createElement("li");
  prevLi.className = `page-item ${auditCurrentPage === 1 ? "disabled" : ""}`;
  prevLi.innerHTML = `
    <a class="page-link" href="#" onclick="loadAuditLog(${
      auditCurrentPage - 1
    })">
      <i class="fas fa-chevron-left"></i>
    </a>
  `;
  pagination.appendChild(prevLi);

  // Page numbers
  for (let i = 1; i <= totalPages; i++) {
    const li = document.createElement("li");
    li.className = `page-item ${i === auditCurrentPage ? "active" : ""}`;
    li.innerHTML = `
      <a class="page-link" href="#" onclick="loadAuditLog(${i})">${i}</a>
    `;
    pagination.appendChild(li);
  }

  // Next button
  const nextLi = document.createElement("li");
  nextLi.className = `page-item ${
    auditCurrentPage === totalPages ? "disabled" : ""
  }`;
  nextLi.innerHTML = `
    <a class="page-link" href="#" onclick="loadAuditLog(${
      auditCurrentPage + 1
    })">
      <i class="fas fa-chevron-right"></i>
    </a>
  `;
  pagination.appendChild(nextLi);
}

function updateAuditUserFilter() {
  const userFilter = document.getElementById("audit-user-filter");
  const currentValue = userFilter.value;

  // Get unique usernames from audit logs
  const usernames = [
    ...new Set(auditLogs.map((log) => log.username).filter(Boolean)),
  ];

  // Clear existing options except first one
  userFilter.innerHTML = '<option value="">Semua User</option>';

  // Add username options
  usernames.forEach((username) => {
    const option = document.createElement("option");
    option.value = username;
    option.textContent = username;
    if (username === currentValue) {
      option.selected = true;
    }
    userFilter.appendChild(option);
  });
}

function showAuditDetail(logId) {
  const log = auditLogs.find((l) => l.id == logId);
  if (!log) return;

  let detailHtml = `
    <div class="modal-header">
      <h5 class="modal-title">Detail Audit Log</h5>
      <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
    </div>
    <div class="modal-body">
      <div class="row">
        <div class="col-md-6">
          <h6>Informasi Umum</h6>
          <table class="table table-sm">
            <tr><td><strong>ID Log:</strong></td><td>${log.id}</td></tr>
            <tr><td><strong>Konsep ID:</strong></td><td><code>${
              log.concept_id
            }</code></td></tr>
            <tr><td><strong>Aksi:</strong></td><td>${getActionBadge(
              log.action
            )}</td></tr>
            <tr><td><strong>User:</strong></td><td>${
              log.username || "Unknown"
            }</td></tr>
            <tr><td><strong>Timestamp:</strong></td><td>${new Date(
              log.timestamp
            ).toLocaleString("id-ID")}</td></tr>
            <tr><td><strong>IP Address:</strong></td><td>${
              log.ip_address || "N/A"
            }</td></tr>
          </table>
        </div>
        <div class="col-md-6">
          <h6>Perubahan</h6>
          <div class="alert alert-info">
            <small>${log.changes || "Tidak ada perubahan yang tercatat"}</small>
          </div>
        </div>
      </div>
  `;

  // Add old data and new data comparison if available
  if (log.old_data || log.new_data) {
    detailHtml += `
      <div class="row mt-3">
        <div class="col-md-6">
          <h6>Data Lama</h6>
          <pre class="bg-light p-2 rounded"><code>${
            JSON.stringify(log.old_data, null, 2) || "N/A"
          }</code></pre>
        </div>
        <div class="col-md-6">
          <h6>Data Baru</h6>
          <pre class="bg-light p-2 rounded"><code>${
            JSON.stringify(log.new_data, null, 2) || "N/A"
          }</code></pre>
        </div>
      </div>
    `;
  }

  detailHtml += `
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
    </div>
  `;

  // Create modal
  const modal = document.createElement("div");
  modal.className = "modal fade";
  modal.id = "auditDetailModal";
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        ${detailHtml}
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  // Clean up modal after hidden
  modal.addEventListener("hidden.bs.modal", () => {
    document.body.removeChild(modal);
  });
}

// ========== END AUDIT TRAIL FUNCTIONS ========== //

// ========== END ADMIN ONTOLOGY JS ==========
