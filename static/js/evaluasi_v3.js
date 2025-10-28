// Evaluasi V3 - Advanced Ensemble Configuration
document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const queryList = document.getElementById("query-list");
  const formAddQuery = document.getElementById("form-add-query");
  const queryText = document.getElementById("query-text");
  const relevantVerseList = document.getElementById("relevant-verse-list");
  const evaluasiBtn = document.getElementById("evaluasi-btn");
  const evaluasiResult = document.getElementById("evaluasi-result");
  const formEvaluasi = document.getElementById("form-evaluasi");
  const inputQueryText = document.getElementById("input-query-text");
  const resetRelevantVersesBtn = document.getElementById(
    "reset-relevant-verses-btn"
  );

  // Advanced Settings Elements
  const toggleAdvancedSettings = document.getElementById(
    "toggle-advanced-settings"
  );
  const advancedSettings = document.getElementById("advanced-settings");
  const ensembleMethod = document.getElementById("ensemble-method");
  const ensembleThreshold = document.getElementById("ensemble-threshold");
  const w2vWeight = document.getElementById("w2v-weight");
  const ftWeight = document.getElementById("ft-weight");
  const gloveWeight = document.getElementById("glove-weight");
  const votingBonus = document.getElementById("voting-bonus");
  const useVotingFilter = document.getElementById("use-voting-filter");

  // Weight value displays
  const w2vWeightVal = document.getElementById("w2v-weight-val");
  const ftWeightVal = document.getElementById("ft-weight-val");
  const gloveWeightVal = document.getElementById("glove-weight-val");
  const w2vImpact = document.getElementById("w2v-impact");
  const ftImpact = document.getElementById("ft-impact");
  const gloveImpact = document.getElementById("glove-impact");

  // View mode elements
  const tableView = document.getElementById("table-view");
  const chartView = document.getElementById("chart-view");
  const comparisonView = document.getElementById("comparison-view");
  const evaluasiChart = document.getElementById("evaluasi-chart");
  const evaluasiComparison = document.getElementById("evaluasi-comparison");

  // Global variables
  let selectedQueryId = null;
  let currentEvaluationResults = null;
  let evaluationChart = null;
  let groundTruthVerses = [];
  let allAyatData = [];
  let currentAyatIndex = 0;
  let ayatLoadLimit = 10;
  let isEvaluating = false;

  // Utility Functions
  function showSpinner(el, msg = "Memuat...") {
    el.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>${msg}</div></div>`;
  }

  function getImpactLabel(weight) {
    if (weight === 0) return "Disabled";
    if (weight < 0.5) return "Low";
    if (weight < 1.0) return "Reduced";
    if (weight === 1.0) return "Normal";
    if (weight <= 1.5) return "Enhanced";
    return "High";
  }

  function updateWeightDisplay(slider, valueDisplay, impactDisplay) {
    const value = parseFloat(slider.value);
    valueDisplay.textContent = value.toFixed(1);
    impactDisplay.textContent = getImpactLabel(value);
  }

  // Event Listeners for Weight Sliders
  w2vWeight.addEventListener("input", () =>
    updateWeightDisplay(w2vWeight, w2vWeightVal, w2vImpact)
  );
  ftWeight.addEventListener("input", () =>
    updateWeightDisplay(ftWeight, ftWeightVal, ftImpact)
  );
  gloveWeight.addEventListener("input", () =>
    updateWeightDisplay(gloveWeight, gloveWeightVal, gloveImpact)
  );

  // Toggle Advanced Settings
  toggleAdvancedSettings.addEventListener("click", function () {
    if (advancedSettings.style.display === "none") {
      advancedSettings.style.display = "block";
      this.innerHTML =
        '<i class="fas fa-cog me-1"></i>Sembunyikan Pengaturan Lanjutan';
    } else {
      advancedSettings.style.display = "none";
      this.innerHTML =
        '<i class="fas fa-cog me-1"></i>Pengaturan Ensemble Lanjutan';
    }
  });

  // Quick Presets
  document.querySelectorAll(".quick-preset-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const preset = this.dataset.preset;
      applyPreset(preset);
    });
  });

  function applyPreset(preset) {
    const presets = {
      balanced: {
        w2v: 1.0,
        ft: 1.0,
        glove: 1.0,
        voting_bonus: 0.05,
        threshold: 0.5,
        use_filter: false,
        method: "weighted",
      },
      precision: {
        w2v: 1.2,
        ft: 1.0,
        glove: 0.8,
        voting_bonus: 0.1,
        threshold: 0.6,
        use_filter: true,
        method: "weighted",
      },
      recall: {
        w2v: 1.0,
        ft: 1.2,
        glove: 1.0,
        voting_bonus: 0.03,
        threshold: 0.4,
        use_filter: false,
        method: "weighted",
      },
      conservative: {
        w2v: 0.8,
        ft: 0.8,
        glove: 1.2,
        voting_bonus: 0.08,
        threshold: 0.65,
        use_filter: true,
        method: "voting",
      },
      aggressive: {
        w2v: 1.5,
        ft: 1.3,
        glove: 1.0,
        voting_bonus: 0.02,
        threshold: 0.35,
        use_filter: false,
        method: "weighted",
      },
    };

    const config = presets[preset];
    if (config) {
      w2vWeight.value = config.w2v;
      ftWeight.value = config.ft;
      gloveWeight.value = config.glove;
      votingBonus.value = config.voting_bonus;
      ensembleThreshold.value = config.threshold;
      useVotingFilter.checked = config.use_filter;
      ensembleMethod.value = config.method;

      // Update displays
      updateWeightDisplay(w2vWeight, w2vWeightVal, w2vImpact);
      updateWeightDisplay(ftWeight, ftWeightVal, ftImpact);
      updateWeightDisplay(gloveWeight, gloveWeightVal, gloveImpact);

      Swal.fire({
        icon: "success",
        title: "Preset Applied!",
        text: `Preset "${preset}" telah diterapkan`,
        timer: 1500,
        showConfirmButton: false,
      });
    }
  }

  // Load Queries
  function loadQueries() {
    showSpinner(queryList, "Memuat query...");
    fetch("/api/query")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          renderQueryList(data.data);
        }
      });
  }

  function renderQueryList(queries) {
    document.getElementById("query-count").textContent = queries.length;
    let html = '<ul class="list-group">';
    queries.forEach((q) => {
      html += `<li class="list-group-item d-flex justify-content-between align-items-center ${
        selectedQueryId === q.id ? "active fw-bold" : ""
      }" style="cursor:pointer" data-id="${q.id}">
                <span>${q.text}</span>
                <div>
                    <button class="btn btn-sm btn-danger btn-delete-query" data-id="${
                      q.id
                    }">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </li>`;
    });
    html += "</ul>";
    queryList.innerHTML = html;

    // Event listeners
    document.querySelectorAll("#query-list .list-group-item").forEach((el) => {
      el.addEventListener("click", function (e) {
        if (e.target.classList.contains("btn-delete-query")) return;
        selectedQueryId = parseInt(this.getAttribute("data-id"));
        loadRelevantVerses(selectedQueryId);
        renderQueryList(queries);
        evaluasiBtn.classList.remove("d-none");
        resetRelevantVersesBtn.classList.remove("d-none");
        resetRelevantVersesBtn.setAttribute("data-id", selectedQueryId);
        evaluasiResult.innerHTML = "";
        formEvaluasi.classList.remove("d-none");

        const q = queries.find((q) => q.id === selectedQueryId);
        if (q) {
          inputQueryText.value = q.text;
          inputQueryText.dataset.queryId = q.id;
        }
      });
    });

    document.querySelectorAll(".btn-delete-query").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const id = parseInt(this.getAttribute("data-id"));
        deleteQuery(id);
      });
    });
  }

  // Add Query
  formAddQuery.addEventListener("submit", function (e) {
    e.preventDefault();
    const text = queryText.value.trim();
    if (!text) return;

    fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          Swal.fire("Berhasil!", "Query berhasil ditambahkan", "success");
          queryText.value = "";
          loadQueries();
        }
      });
  });

  // Delete Query
  function deleteQuery(id) {
    Swal.fire({
      title: "Hapus Query?",
      text: "Data evaluasi terkait akan ikut terhapus!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Ya, Hapus!",
      cancelButtonText: "Batal",
    }).then((result) => {
      if (result.isConfirmed) {
        fetch(`/api/query/${id}`, { method: "DELETE" })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              Swal.fire("Terhapus!", "Query berhasil dihapus", "success");
              loadQueries();
              if (selectedQueryId === id) {
                selectedQueryId = null;
                relevantVerseList.innerHTML = "";
                evaluasiResult.innerHTML = "";
                formEvaluasi.classList.add("d-none");
              }
            }
          });
      }
    });
  }

  // Load Relevant Verses
  function loadRelevantVerses(queryId) {
    showSpinner(relevantVerseList, "Memuat ayat relevan...");
    fetch(`/api/query/${queryId}/relevant_verses`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          groundTruthVerses = data.data.map((v) => v.verse_ref);
          renderRelevantVerses(data.data);
          document.getElementById("ayat-count").textContent = data.data.length;
        }
      });
  }

  function renderRelevantVerses(verses) {
    if (verses.length === 0) {
      relevantVerseList.innerHTML =
        '<div class="alert alert-info">Belum ada ayat relevan. Silakan tambahkan.</div>';
      return;
    }

    // Jika data banyak, tampilkan ringkas (seperti V2)
    let html = "";
    if (verses.length <= 100) {
      verses.forEach((v) => {
        html += `<span class="badge bg-primary me-1 mb-1 badge-ayat-ref" data-ref="${v.verse_ref}" style="cursor:pointer">${v.verse_ref}</span>`;
      });
    } else {
      const preview = verses.slice(0, 10);
      preview.forEach((v) => {
        html += `<span class="badge bg-primary me-1 mb-1 badge-ayat-ref" data-ref="${v.verse_ref}" style="cursor:pointer">${v.verse_ref}</span>`;
      });
      const sisa = verses.length - 10;
      html += `<span class="badge bg-secondary me-1 mb-1 badge-ayat-more" style="cursor:pointer">... dan ${sisa} ayat lain</span>`;
    }
    // Tambahkan kontrol hapus cepat terakhir (opsional) sebagai list sederhana di bawah jika jumlah <= 100
    if (verses.length <= 100) {
      html += '<div class="mt-2">';
      verses.forEach((v) => {
        html += `<button class="btn btn-sm btn-outline-danger me-1 mb-1 btn-delete-verse" data-id="${v.id}" data-query-id="${v.query_id}"><i class="fas fa-trash"></i> ${v.verse_ref}</button>`;
      });
      html += '</div>';
    } else {
      // Untuk data besar, arahkan pengguna ke modal detail untuk aksi hapus
      html += '<div class="form-text mt-1">Gunakan "Detail Ayat Relevan" untuk kelola/hapus.</div>';
    }

    relevantVerseList.innerHTML = html;

    // Klik badge ayat: buka modal detail (mirip V2)
    relevantVerseList.querySelectorAll('.badge-ayat-ref').forEach((badge) => {
      badge.addEventListener('click', function () {
        if (!selectedQueryId) return;
        showAllAyatDetailModal(selectedQueryId);
      });
    });

    // Klik badge more: buka modal detail semua ayat
    const badgeMore = relevantVerseList.querySelector('.badge-ayat-more');
    if (badgeMore) {
      badgeMore.addEventListener('click', function () {
        if (!selectedQueryId) return;
        showAllAyatDetailModal(selectedQueryId);
      });
    }

    // Hapus cepat (hanya render saat <= 100)
    document.querySelectorAll(".btn-delete-verse").forEach((btn) => {
      btn.addEventListener("click", function () {
        const id = this.dataset.id;
        const queryId = this.dataset.queryId;
        deleteRelevantVerse(id, queryId);
      });
    });
  }

  function deleteRelevantVerse(id, queryId) {
    fetch(`/api/query/relevant_verse/${id}`, { method: "DELETE" })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          Swal.fire("Terhapus!", "Ayat relevan berhasil dihapus", "success");
          loadRelevantVerses(queryId);
        }
      });
  }

  // Detail Ayat Relevan (Modal) mirip V2 namun disederhanakan
  evaluasiBtn.addEventListener("click", function () {
    if (!selectedQueryId) {
      Swal.fire("Info", "Pilih query terlebih dahulu", "info");
      return;
    }
    showAllAyatDetailModal(selectedQueryId);
  });

  async function showAllAyatDetailModal(queryId) {
    const ayatDetailContent = document.getElementById("ayat-detail-content");
    const modalEl = document.getElementById("ayatDetailModal");
    const modal = new bootstrap.Modal(modalEl);
    showSpinner(ayatDetailContent, "Memuat detail ayat...");

    try {
      const res = await fetch(`/api/query/${queryId}/relevant_verses`);
      const data = await res.json();
      if (!data.success || data.data.length === 0) {
        ayatDetailContent.innerHTML =
          '<div class="text-muted">Tidak ada ayat relevan.</div>';
        document.getElementById('load-more-container').classList.add('d-none');
        modal.show();
        return;
      }

      allAyatData = data.data;
      currentAyatIndex = 0;
      document.getElementById('total-count').textContent = allAyatData.length;
      document.getElementById('loaded-count').textContent = '0';

      let html = '<ul class="list-group mb-3"></ul>';
      ayatDetailContent.innerHTML = html;

      const loadMoreContainer = document.getElementById('load-more-container');
      if (allAyatData.length > 0) {
        loadMoreContainer.classList.remove('d-none');
      } else {
        loadMoreContainer.classList.add('d-none');
      }

      await loadMoreAyat();
      modal.show();
    } catch (e) {
      ayatDetailContent.innerHTML =
        '<div class="text-danger">Gagal memuat ayat relevan.</div>';
      document.getElementById('load-more-container').classList.add('d-none');
      modal.show();
    }
  }

  async function loadMoreAyat() {
    const container = document.querySelector('#ayat-detail-content ul');
    if (!container) return;

    const loadMoreBtn = document.getElementById('load-more-btn');
    const loadMoreText = document.getElementById('load-more-text');
    const loadMoreSpinner = document.getElementById('load-more-spinner');

    loadMoreBtn.disabled = true;
    loadMoreText.classList.add('d-none');
    loadMoreSpinner.classList.remove('d-none');

    const endIndex = Math.min(currentAyatIndex + ayatLoadLimit, allAyatData.length);
    for (let i = currentAyatIndex; i < endIndex; i++) {
      const v = allAyatData[i];
      const [surah, ayat] = v.verse_ref.split(":");
      let itemHtml = `<li class='list-group-item d-flex justify-content-between align-items-center' data-id='${v.id}'>`;
      try {
        const r = await fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`);
        const j = await r.json();
        if (j.success && j.ayat) {
          itemHtml += `
            <div>
              <div><strong>${v.verse_ref}</strong></div>
              <div class='text-arab small' style='font-size:1em'>${j.ayat.text}</div>
              <div class='text-muted small'><em>${j.ayat.translation || ''}</em></div>
            </div>`;
        } else {
          itemHtml += `
            <div>
              <div><strong>${v.verse_ref}</strong></div>
              <div class='text-danger small'>Detail ayat tidak ditemukan</div>
            </div>`;
        }
      } catch (_) {
        itemHtml += `
          <div>
            <div><strong>${v.verse_ref}</strong></div>
            <div class='text-danger small'>Gagal memuat detail</div>
          </div>`;
      }
      itemHtml += `
        <button class='btn btn-sm btn-danger btn-delete-verse-modal' data-id='${v.id}'>
          <i class='fas fa-trash'></i>
        </button>`;
      itemHtml += `</li>`;
      container.insertAdjacentHTML('beforeend', itemHtml);
    }

    currentAyatIndex = endIndex;
    document.getElementById('loaded-count').textContent = currentAyatIndex.toString();

    const loadMoreContainer = document.getElementById('load-more-container');
    if (currentAyatIndex >= allAyatData.length) {
      loadMoreContainer.classList.add('d-none');
    } else {
      loadMoreContainer.classList.remove('d-none');
    }

    loadMoreBtn.disabled = false;
    loadMoreText.classList.remove('d-none');
    loadMoreSpinner.classList.add('d-none');

    document.querySelectorAll('.btn-delete-verse-modal').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-id');
        const ayatDetailContent = document.getElementById('ayat-detail-content');
        showSpinner(ayatDetailContent, 'Menghapus ayat...');
        fetch(`/api/query/relevant_verse/${id}`, { method: 'DELETE' })
          .then((res) => res.json())
          .then(() => {
            showAllAyatDetailModal(selectedQueryId);
            loadRelevantVerses(selectedQueryId);
          });
      });
    });
  }

  document.getElementById('load-more-btn').addEventListener('click', function() {
    loadMoreAyat();
  });

  // Tambah ayat dari modal
  document
    .getElementById("form-add-verse-modal")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      if (!selectedQueryId) return;
      const input = document.getElementById("verse-ref-modal");
      const verse = (input.value || "").trim();
      if (!verse) return;
      const ayatDetailContent = document.getElementById("ayat-detail-content");
      showSpinner(ayatDetailContent, "Menambah ayat...");
      fetch(`/api/query/${selectedQueryId}/relevant_verses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verse_ref: verse }),
      })
        .then((res) => res.json())
        .then(() => {
          input.value = "";
          showAllAyatDetailModal(selectedQueryId);
          loadRelevantVerses(selectedQueryId);
        });
    });

  document.getElementById('load-more-btn').addEventListener('click', function() {
    loadMoreAyat();
  });

  // Select All Methods
  document.querySelectorAll(".select-all-methods").forEach((btn) => {
    btn.addEventListener("click", function () {
      const checkboxes = document.querySelectorAll(".eval-method");
      const allChecked = Array.from(checkboxes).every((cb) => cb.checked);
      checkboxes.forEach((cb) => (cb.checked = !allChecked));
    });
  });

  // Run Evaluation
  formEvaluasi.addEventListener("submit", function (e) {
    e.preventDefault();
    if (isEvaluating) {
      Swal.fire("Info", "Evaluasi sedang berjalan, tunggu hingga selesai.", "info");
      return;
    }

    if (!selectedQueryId) {
      Swal.fire("Error", "Pilih query terlebih dahulu", "error");
      return;
    }

    const queryTextVal = inputQueryText.value.trim();
    if (!queryTextVal) {
      Swal.fire("Error", "Query text tidak boleh kosong", "error");
      return;
    }

    // Get selected methods
    const selectedMethods = Array.from(
      document.querySelectorAll(".eval-method:checked")
    ).map((cb) => cb.value);

    if (selectedMethods.length === 0) {
      Swal.fire("Error", "Pilih minimal satu metode evaluasi", "error");
      return;
    }

    // Get ensemble configuration
    const ensembleConfig = {
      method: ensembleMethod.value,
      w2v_weight: parseFloat(w2vWeight.value),
      ft_weight: parseFloat(ftWeight.value),
      glove_weight: parseFloat(gloveWeight.value),
      voting_bonus: parseFloat(votingBonus.value),
      use_voting_filter: useVotingFilter.checked,
    };

    const resultLimit = parseInt(document.getElementById("result-limit").value);

    const payload = {
      query_text: queryTextVal,
      result_limit: resultLimit,
      selected_methods: selectedMethods,
      ensemble_config: ensembleConfig,
      threshold_per_model: {
        ensemble: parseFloat(ensembleThreshold.value),
        word2vec: 0.5,
        fasttext: 0.5,
        glove: 0.5,
        lexical: 0.0,
      },
    };

    // Show loading and disable inputs
    showSpinner(evaluasiResult, "Menjalankan evaluasi...");
    isEvaluating = true;
    const runBtn = formEvaluasi.querySelector('button[type="submit"]');
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Memproses...';
    }
    // Optionally disable form fields to avoid changes mid-run
    const disabledEls = Array.from(formEvaluasi.querySelectorAll('input, select, button'));
    disabledEls.forEach(el => { if (el !== runBtn) el.disabled = true; });

    fetch(`/api/evaluation_v3/${selectedQueryId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          currentEvaluationResults = data;
          renderEvaluationResults(data);

          Swal.fire({
            icon: "success",
            title: "Evaluasi Selesai!",
            text: `${data.results.length} metode telah dievaluasi`,
            timer: 2000,
            showConfirmButton: false,
          });
        } else {
          evaluasiResult.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
      })
      .catch((err) => {
        evaluasiResult.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
      })
      .finally(() => {
        isEvaluating = false;
        if (runBtn) {
          runBtn.disabled = false;
          runBtn.innerHTML = '<i class="fas fa-play me-2"></i>Jalankan Evaluasi';
        }
        disabledEls.forEach(el => { if (el) el.disabled = false; });
      });
  });

  // Render Evaluation Results
  function renderEvaluationResults(data) {
    const results = data.results;
    const ensembleComparison = data.ensemble_comparison || {};
    const ensembleAnalysis = data.ensemble_analysis;

    let html =
      '<div class="table-responsive"><table class="table table-striped table-hover align-middle">';
    html += '<thead class="table-dark"><tr>';
    html +=
      "<th>Metode</th><th>Precision</th><th>Recall</th><th>F1-Score</th><th>Accuracy</th>";
    html +=
      "<th>TP</th><th>FP</th><th>FN</th><th>Time (s)</th><th>Found</th></tr></thead><tbody>";

    results.forEach((r) => {
      if (r.error) {
        html += `<tr><td colspan="10" class="text-danger">${r.label}: ${r.error}</td></tr>`;
      } else {
        const isWinner =
          ensembleAnalysis &&
          (r.method === ensembleAnalysis.best_f1[0] ||
            r.method === ensembleAnalysis.best_precision[0] ||
            r.method === ensembleAnalysis.best_recall[0]);

        html += `<tr ${isWinner ? 'class="table-success"' : ""}>`;
        html += `<td><strong>${r.label}</strong>`;
        if (isWinner) html += ' <span class="badge bg-success">★</span>';
        html += `</td>`;
        html += `<td>${(r.precision * 100).toFixed(1)}%</td>`;
        html += `<td>${(r.recall * 100).toFixed(1)}%</td>`;
        html += `<td>${(r.f1 * 100).toFixed(1)}%</td>`;
        html += `<td>${(r.accuracy * 100).toFixed(1)}%</td>`;
        html += `<td>${r.true_positive}</td>`;
        html += `<td>${r.false_positive}</td>`;
        html += `<td>${r.false_negative}</td>`;
        html += `<td>${r.exec_time}</td>`;
        html += `<td>${r.total_found}</td>`;
        html += "</tr>";
      }
    });

    html += "</tbody></table></div>";

    // Ensemble Comparison Summary
    if (Object.keys(ensembleComparison).length > 1) {
      html +=
        '<div class="mt-4"><h5><i class="fas fa-trophy me-2 text-warning"></i>Perbandingan Metode Ensemble</h5>';
      html += '<div class="row g-3">';

      Object.entries(ensembleComparison).forEach(([method, result]) => {
        html += `<div class="col-md-4">
                    <div class="card metric-card">
                        <div class="card-body">
                            <h6 class="card-title">${method}</h6>
                            <div class="mb-2">
                                <small class="text-muted">F1-Score:</small>
                                <strong class="d-block">${(
                                  result.f1 * 100
                                ).toFixed(1)}%</strong>
                            </div>
                            <div class="mb-2">
                                <small class="text-muted">Precision:</small>
                                <strong class="d-block">${(
                                  result.precision * 100
                                ).toFixed(1)}%</strong>
                            </div>
                            <div>
                                <small class="text-muted">Recall:</small>
                                <strong class="d-block">${(
                                  result.recall * 100
                                ).toFixed(1)}%</strong>
                            </div>
                        </div>
                    </div>
                </div>`;
      });

      html += "</div></div>";
    }

    evaluasiResult.innerHTML = html;
  }

  // View Mode Switching
  tableView.addEventListener("change", function () {
    if (this.checked) {
      evaluasiResult.classList.remove("d-none");
      evaluasiChart.classList.add("d-none");
      evaluasiComparison.classList.add("d-none");
    }
  });

  chartView.addEventListener("change", function () {
    if (this.checked && currentEvaluationResults) {
      evaluasiResult.classList.add("d-none");
      evaluasiChart.classList.remove("d-none");
      evaluasiComparison.classList.add("d-none");
      renderChart(currentEvaluationResults);
    }
  });

  comparisonView.addEventListener("change", function () {
    if (this.checked && currentEvaluationResults) {
      evaluasiResult.classList.add("d-none");
      evaluasiChart.classList.add("d-none");
      evaluasiComparison.classList.remove("d-none");
      renderComparison(currentEvaluationResults);
    }
  });

  // Render Chart
  function renderChart(data) {
    const results = data.results.filter((r) => !r.error);
    const labels = results.map((r) => r.label);
    const precision = results.map((r) => r.precision * 100);
    const recall = results.map((r) => r.recall * 100);
    const f1 = results.map((r) => r.f1 * 100);

    if (evaluationChart) {
      evaluationChart.destroy();
      evaluationChart = null;
    }

    // Ensure a canvas exists inside the chart container div
    const container = evaluasiChart; // this is a div
    container.innerHTML = '<canvas id="evaluasi-chart-canvas"></canvas>';
    const canvas = document.getElementById('evaluasi-chart-canvas');
    const ctx = canvas.getContext('2d');

    evaluationChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Precision (%)",
            data: precision,
            backgroundColor: "rgba(40, 167, 69, 0.7)",
            borderColor: "rgba(40, 167, 69, 1)",
            borderWidth: 1,
          },
          {
            label: "Recall (%)",
            data: recall,
            backgroundColor: "rgba(23, 162, 184, 0.7)",
            borderColor: "rgba(23, 162, 184, 1)",
            borderWidth: 1,
          },
          {
            label: "F1-Score (%)",
            data: f1,
            backgroundColor: "rgba(255, 193, 7, 0.7)",
            borderColor: "rgba(255, 193, 7, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
          },
        },
      },
    });
  }

  // Render Comparison View
  function renderComparison(data) {
    const ensembleResults = data.results.filter(
      (r) => r.method && r.method.includes("ensemble") && !r.error
    );

    if (ensembleResults.length === 0) {
      evaluasiComparison.innerHTML =
        '<div class="alert alert-info">Tidak ada data ensemble untuk dibandingkan</div>';
      return;
    }

    let html =
      '<h5 class="mb-3"><i class="fas fa-columns me-2"></i>Perbandingan Detail Metode Ensemble</h5>';
    html += '<div class="row g-3">';

    ensembleResults.forEach((r) => {
      html += `<div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">${r.label}</h6>
                    </div>
                    <div class="card-body">
                        <div class="row g-2">
                            <div class="col-6">
                                <div class="metric-card precision p-3">
                                    <small class="text-muted">Precision</small>
                                    <h4 class="mb-0">${(
                                      r.precision * 100
                                    ).toFixed(1)}%</h4>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="metric-card recall p-3">
                                    <small class="text-muted">Recall</small>
                                    <h4 class="mb-0">${(r.recall * 100).toFixed(
                                      1
                                    )}%</h4>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="metric-card f1 p-3">
                                    <small class="text-muted">F1-Score</small>
                                    <h4 class="mb-0">${(r.f1 * 100).toFixed(
                                      1
                                    )}%</h4>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="metric-card p-3" style="border-left-color: #6c757d;">
                                    <small class="text-muted">Time</small>
                                    <h4 class="mb-0">${r.exec_time}s</h4>
                                </div>
                            </div>
                        </div>
                        ${
                          r.weights
                            ? `
                        <div class="mt-3">
                            <small class="text-muted d-block mb-2">Weights:</small>
                            <div class="d-flex justify-content-between">
                                <span>W2V: ${r.weights.word2vec}</span>
                                <span>FT: ${r.weights.fasttext}</span>
                                <span>GloVe: ${r.weights.glove}</span>
                            </div>
                        </div>
                        `
                            : ""
                        }
                    </div>
                </div>
            </div>`;
    });

    html += "</div>";
    evaluasiComparison.innerHTML = html;
  }

  // Export to Excel
  document
    .getElementById("export-evaluasi-btn")
    .addEventListener("click", function () {
      if (!currentEvaluationResults) {
        Swal.fire("Info", "Belum ada hasil evaluasi untuk di-export", "info");
        return;
      }

      Swal.fire("Info", "Fitur export akan segera tersedia", "info");
    });

  // Initialize
  loadQueries();
});
