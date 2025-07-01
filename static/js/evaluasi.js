document.addEventListener("DOMContentLoaded", function () {
  const queryList = document.getElementById("query-list");
  const formAddQuery = document.getElementById("form-add-query");
  const queryText = document.getElementById("query-text");
  const relevantVerseSection = document.getElementById(
    "relevant-verse-section"
  );
  const relevantVerseList = document.getElementById("relevant-verse-list");
  const evaluasiBtn = document.getElementById("evaluasi-btn");
  const evaluasiResult = document.getElementById("evaluasi-result");
  const logBtn = document.getElementById("log-btn");
  const logModal = new bootstrap.Modal(document.getElementById("logModal"));
  const logContent = document.getElementById("log-content");
  const ayatDetailModal = new bootstrap.Modal(
    document.getElementById("ayatDetailModal")
  );
  const ayatDetailContent = document.getElementById("ayat-detail-content");
  const formEvaluasi = document.getElementById("form-evaluasi");
  const inputQueryText = document.getElementById("input-query-text");
  const inputResultLimit = document.getElementById("input-result-limit");
  const inputThreshold = document.getElementById("input-threshold");

  let selectedQueryId = null;

  function showSpinner(el, msg = "Memuat...") {
    el.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>${msg}</div></div>`;
  }

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
          <button class="btn btn-sm btn-info btn-detail-query me-2" data-id="${
            q.id
          }"><i class="fas fa-list"></i> Detail</button>
          <button class="btn btn-sm btn-danger btn-delete-query" data-id="${
            q.id
          }"><i class="fas fa-trash"></i></button>
        </div>
      </li>`;
    });
    html += "</ul>";
    queryList.innerHTML = html;
    // Event pilih query
    document.querySelectorAll("#query-list .list-group-item").forEach((el) => {
      el.addEventListener("click", function (e) {
        if (
          e.target.classList.contains("btn-delete-query") ||
          e.target.classList.contains("btn-detail-query")
        )
          return;
        selectedQueryId = parseInt(this.getAttribute("data-id"));
        loadRelevantVerses(selectedQueryId);
        renderQueryList(queries);
        evaluasiBtn.classList.remove("d-none");
        logBtn.classList.remove("d-none");
        evaluasiResult.innerHTML = "";
        loadEvaluationResults(selectedQueryId);
        // Tampilkan form evaluasi
        formEvaluasi.classList.remove("d-none");
        // Autoisi query_text jika ada di list
        const q = queries.find((q) => q.id === selectedQueryId);
        if (q) inputQueryText.value = q.text;
      });
    });
    // Event hapus query
    document.querySelectorAll(".btn-delete-query").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const id = this.getAttribute("data-id");
        if (confirm("Hapus query ini beserta ayat relevannya?")) {
          fetch(`/api/query/${id}`, { method: "DELETE" })
            .then((res) => res.json())
            .then(() => {
              if (selectedQueryId == id) {
                selectedQueryId = null;
                relevantVerseList.innerHTML = "";
                evaluasiBtn.classList.add("d-none");
                logBtn.classList.add("d-none");
                evaluasiResult.innerHTML = "";
                document.getElementById("ayat-count").textContent = 0;
              }
              loadQueries();
            });
        }
      });
    });
    // Event detail query
    document.querySelectorAll(".btn-detail-query").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const id = this.getAttribute("data-id");
        showAllAyatDetailModal(id);
      });
    });
  }

  async function showAllAyatDetailModal(queryId) {
    showSpinner(ayatDetailContent, "Memuat detail ayat...");
    // Ambil semua ayat relevan
    const res = await fetch(`/api/query/${queryId}/relevant_verses`);
    const data = await res.json();
    if (!data.success) {
      ayatDetailContent.innerHTML =
        '<div class="text-danger">Gagal memuat ayat relevan.</div>';
      ayatDetailModal.show();
      return;
    }
    if (!data.data.length) {
      ayatDetailContent.innerHTML =
        '<div class="text-muted">Tidak ada ayat relevan.</div>';
      ayatDetailModal.show();
      return;
    }
    // Fetch detail semua ayat
    let html = '<ul class="list-group mb-3">';
    for (const v of data.data) {
      const [surah, ayat] = v.verse_ref.split(":");
      try {
        showSpinner(ayatDetailContent, "Memuat detail ayat...");
        const detailRes = await fetch(
          `/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`
        );
        const detailData = await detailRes.json();
        if (detailData.success && detailData.ayat) {
          const a = detailData.ayat;
          html += `<li class='list-group-item d-flex justify-content-between align-items-center'>
            <div>
              <div><strong>${a.surah_name} (${a.surah}) : ${
            a.ayat
          }</strong></div>
              <div class='text-arab' style='font-size:1.2em'>${a.text}</div>
              <div><em>${a.translation || ""}</em></div>
            </div>
            <button class='btn btn-sm btn-danger btn-delete-verse-modal' data-id='${
              v.id
            }'><i class='fas fa-trash'></i></button>
          </li>`;
        } else {
          html += `<li class='list-group-item text-danger'>Detail ayat tidak ditemukan untuk ${v.verse_ref}.</li>`;
        }
      } catch {
        html += `<li class='list-group-item text-danger'>Gagal memuat detail ayat untuk ${v.verse_ref}.</li>`;
      }
    }
    html += "</ul>";
    ayatDetailContent.innerHTML = html;
    ayatDetailModal.show();
    // Event hapus ayat di modal
    document.querySelectorAll(".btn-delete-verse-modal").forEach((btn) => {
      btn.addEventListener("click", function () {
        const id = this.getAttribute("data-id");
        showSpinner(ayatDetailContent, "Menghapus ayat...");
        fetch(`/api/query/relevant_verse/${id}`, { method: "DELETE" })
          .then((res) => res.json())
          .then(() => showAllAyatDetailModal(queryId));
      });
    });
  }

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
      .then(() => {
        queryText.value = "";
        loadQueries();
      });
  });

  function loadRelevantVerses(queryId) {
    fetch(`/api/query/${queryId}/relevant_verses`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          renderRelevantVerses(data.data);
          document.getElementById("ayat-count").textContent = data.data.length;
        }
      });
  }

  function renderRelevantVerses(verses) {
    // Tampilkan setiap ayat sebagai badge
    let html = "";
    verses.forEach((v) => {
      html += `<span class="badge bg-primary me-1 mb-1 badge-ayat-ref" data-ref="${v.verse_ref}" style="cursor:pointer">${v.verse_ref}</span>`;
    });
    relevantVerseList.innerHTML = html;
    // Tambahkan event listener untuk badge ayat
    relevantVerseList.querySelectorAll(".badge-ayat-ref").forEach((badge) => {
      badge.addEventListener("click", function (e) {
        e.stopPropagation();
        const ref = this.getAttribute("data-ref");
        // Tampilkan loading di modal
        const modalBody = document.getElementById("found-verses-content");
        modalBody.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>Memuat detail ayat...</div></div>`;
        const modal = new bootstrap.Modal(
          document.getElementById("modalFoundVerses")
        );
        modal.show();
        // Ambil detail ayat via AJAX
        const [surah, ayat] = ref.split(":");
        fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`)
          .then((res) => res.json())
          .then((data) => {
            if (data.success && data.ayat) {
              const a = data.ayat;
              modalBody.innerHTML = `
                <div><strong>${a.surah_name} (${a.surah}) : ${
                a.ayat
              }</strong></div>
                <div class='text-arab' style='font-size:1.2em'>${a.text}</div>
                <div><em>${a.translation || ""}</em></div>
              `;
            } else {
              modalBody.innerHTML = `<div class='text-danger'>Detail ayat tidak ditemukan.</div>`;
            }
          })
          .catch(() => {
            modalBody.innerHTML = `<div class='text-danger'>Gagal memuat detail ayat.</div>`;
          });
      });
    });
  }

  // Form tambah ayat di modal
  document
    .getElementById("form-add-verse-modal")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      const verse = document.getElementById("verse-ref-modal").value.trim();
      if (!verse || !selectedQueryId) return;
      showSpinner(ayatDetailContent, "Menambah ayat...");
      fetch(`/api/query/${selectedQueryId}/relevant_verses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verse_ref: verse }),
      })
        .then((res) => res.json())
        .then(() => {
          document.getElementById("verse-ref-modal").value = "";
          showAllAyatDetailModal(selectedQueryId);
          loadRelevantVerses(selectedQueryId);
        });
    });

  // Tampilkan form tambah ayat hanya jika query dipilih
  queryList.addEventListener("click", function () {
    if (selectedQueryId) {
      evaluasiBtn.classList.remove("d-none");
      logBtn.classList.remove("d-none");
    }
  });

  // Select All functionality
  const selectAllBtn = document.getElementById("select-all-methods");
  if (selectAllBtn) {
    selectAllBtn.addEventListener("click", function () {
      document
        .querySelectorAll(".eval-method")
        .forEach((cb) => (cb.checked = true));
    });
  }

  formEvaluasi.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!selectedQueryId) return;
    const query_text = inputQueryText.value.trim();
    const result_limit = parseInt(inputResultLimit.value) || 10;
    const threshold = parseFloat(inputThreshold.value) || 0.5;
    // Ambil metode yang dipilih
    const selectedMethods = Array.from(
      document.querySelectorAll(".eval-method:checked")
    ).map((cb) => cb.value);
    if (!query_text) {
      alert("Query evaluasi wajib diisi!");
      return;
    }
    if (selectedMethods.length === 0) {
      alert("Pilih minimal satu metode evaluasi!");
      return;
    }
    showSpinner(evaluasiResult, "Menjalankan evaluasi...");
    fetch(`/api/evaluation/${selectedQueryId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text,
        result_limit,
        threshold,
        selected_methods: selectedMethods,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          // Hitung summary
          let bestIdx = -1;
          let bestF1 = -1;
          let sumPrecision = 0,
            sumRecall = 0,
            sumF1 = 0,
            count = 0;
          data.results.forEach((r, idx) => {
            if (!r.error) {
              sumPrecision += parseFloat(r.precision);
              sumRecall += parseFloat(r.recall);
              sumF1 += parseFloat(r.f1);
              count++;
              if (parseFloat(r.f1) > bestF1) {
                bestF1 = parseFloat(r.f1);
                bestIdx = idx;
              }
            }
          });
          let avgPrecision = count ? (sumPrecision / count).toFixed(2) : "-";
          let avgRecall = count ? (sumRecall / count).toFixed(2) : "-";
          let avgF1 = count ? (sumF1 / count).toFixed(2) : "-";
          let bestLabel = bestIdx >= 0 ? data.results[bestIdx].label : "-";
          let bestF1Str = bestF1 >= 0 ? bestF1.toFixed(2) : "-";
          // Summary HTML
          let summaryHtml = `<div class='mb-2 p-2 bg-light border rounded' id='eval-summary'>
            <strong>Metode terbaik:</strong> ${bestLabel} (F1: ${bestF1Str})<br>
            <strong>Rata-rata</strong> &mdash; Precision: ${avgPrecision} | Recall: ${avgRecall} | F1: ${avgF1}
          </div>`;
          // Tabel hasil
          let html =
            '<table class="table table-bordered table-sm"><thead><tr>' +
            "<th>Metode</th><th>TP</th><th>FP</th><th>FN</th><th>Precision</th><th>Recall</th><th>F1</th><th>Waktu (s)</th><th>Total Ditemukan</th><th>Ayat Hasil</th></tr></thead><tbody>";
          data.results.forEach((r, idx) => {
            if (r.error) {
              html += `<tr><td colspan='10' class='text-danger'>${r.label}: ${r.error}</td></tr>`;
            } else {
              let highlight = idx === bestIdx ? "table-warning fw-bold" : "";
              html +=
                `<tr class='${highlight}'><td>${r.label}</td><td>${r.true_positive}</td><td>${r.false_positive}</td><td>${r.false_negative}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td><td>${r.exec_time}</td><td>${r.total_found}</td>` +
                `<td><button class='btn btn-sm btn-info btn-show-found-verses' data-idx='${idx}'>Lihat</button></td></tr>`;
            }
          });
          html += "</tbody></table>";
          evaluasiResult.innerHTML = summaryHtml + html;

          // Event listener tombol lihat ayat hasil
          document.querySelectorAll(".btn-show-found-verses").forEach((btn) => {
            btn.addEventListener("click", function () {
              const idx = this.getAttribute("data-idx");
              const found = data.results[idx].found_verses || [];
              // Ambil ground_truth jika tersedia
              const groundTruth = data.results[idx].ground_truth || [];
              let content = "";
              if (found.length === 0) {
                content =
                  '<div class="text-muted">Tidak ada ayat ditemukan.</div>';
              } else {
                content = '<div class="d-flex flex-wrap gap-1">';
                found.forEach((ref) => {
                  // Cek apakah TP atau FP
                  let isTP = groundTruth.includes
                    ? groundTruth.includes(ref)
                    : false;
                  let badgeClass = isTP ? "bg-primary" : "bg-secondary";
                  let badgeLabel = isTP ? "TP" : "FP";
                  content += `<span class='badge ${badgeClass} badge-ayat-ref' data-ref='${ref}' style='cursor:pointer'>${ref} <span style='font-size:0.8em;'>(${badgeLabel})</span></span>`;
                });
                content += "</div>";
              }
              // Cari baris <tr> terdekat, lalu cari atau buat baris baru setelahnya
              const tr = this.closest("tr");
              let nextTr = tr.nextElementSibling;
              if (!nextTr || !nextTr.classList.contains("found-verses-row")) {
                nextTr = document.createElement("tr");
                nextTr.className = "found-verses-row";
                nextTr.innerHTML = `<td colspan='10'></td>`;
                tr.parentNode.insertBefore(nextTr, tr.nextSibling);
              }
              // Toggle tampil/sembunyi
              const td = nextTr.querySelector("td");
              if (nextTr.style.display === "table-row") {
                nextTr.style.display = "none";
              } else {
                td.innerHTML = content;
                nextTr.style.display = "table-row";
              }
              // Setelah badge dibuat, tambahkan event listener untuk badge ayat
              setTimeout(() => {
                nextTr.querySelectorAll(".badge-ayat-ref").forEach((badge) => {
                  badge.addEventListener("click", function (e) {
                    e.stopPropagation();
                    const ref = this.getAttribute("data-ref");
                    // Tampilkan loading di modal
                    const modalBody = document.getElementById(
                      "found-verses-content"
                    );
                    modalBody.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>Memuat detail ayat...</div></div>`;
                    const modal = new bootstrap.Modal(
                      document.getElementById("modalFoundVerses")
                    );
                    modal.show();
                    // Ambil detail ayat via AJAX
                    const [surah, ayat] = ref.split(":");
                    fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`)
                      .then((res) => res.json())
                      .then((data) => {
                        if (data.success && data.ayat) {
                          const a = data.ayat;
                          modalBody.innerHTML = `
                            <div><strong>${a.surah_name} (${a.surah}) : ${
                            a.ayat
                          }</strong></div>
                            <div class='text-arab' style='font-size:1.2em'>${
                              a.text
                            }</div>
                            <div><em>${a.translation || ""}</em></div>
                          `;
                        } else {
                          modalBody.innerHTML = `<div class='text-danger'>Detail ayat tidak ditemukan.</div>`;
                        }
                      })
                      .catch(() => {
                        modalBody.innerHTML = `<div class='text-danger'>Gagal memuat detail ayat.</div>`;
                      });
                  });
                });
              }, 10);
            });
          });
        } else {
          evaluasiResult.innerHTML = `<div class='alert alert-danger'>${data.message}</div>`;
        }
      })
      .catch(() => {
        evaluasiResult.innerHTML = `<div class='alert alert-danger'>Terjadi kesalahan saat evaluasi.</div>`;
      });
  });

  function loadEvaluationResults(queryId) {
    showSpinner(evaluasiResult, "Memuat hasil evaluasi...");
    fetch(`/api/query/${queryId}/evaluation_results`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.results.length > 0) {
          let html = "<h5>Hasil Evaluasi Terakhir</h5>";
          html +=
            '<table class="table table-bordered"><thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>Waktu (s)</th></tr></thead><tbody>';
          data.results.forEach((r) => {
            html += `<tr><td>${r.model}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td><td>${r.exec_time}</td></tr>`;
          });
          html += "</tbody></table>";
          evaluasiResult.innerHTML = html;
        } else {
          evaluasiResult.innerHTML = "";
        }
      });
  }

  logBtn.addEventListener("click", function () {
    if (!selectedQueryId) return;
    showSpinner(logContent, "Memuat log...");
    fetch(`/api/query/${selectedQueryId}/evaluation_logs`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.logs.length > 0) {
          let html =
            '<table class="table table-sm table-bordered"><thead><tr><th>Waktu</th><th>Model</th><th>Skor Lama</th><th>Skor Baru</th></tr></thead><tbody>';
          data.logs.forEach((l) => {
            html += `<tr><td>${l.changed_at}</td><td>${l.model}</td><td>${l.old_score}</td><td>${l.new_score}</td></tr>`;
          });
          html += "</tbody></table>";
          logContent.innerHTML = html;
        } else {
          logContent.innerHTML =
            '<div class="text-muted">Belum ada log perubahan.</div>';
        }
      });
    logModal.show();
  });

  loadQueries();
});
