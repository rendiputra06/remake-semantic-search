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
    const resetRelevantVersesBtn = document.getElementById(
        "reset-relevant-verses-btn"
    );
    const logModal = new bootstrap.Modal(document.getElementById("logModal"));
    const logContent = document.getElementById("log-content");
    const ayatDetailModal = new bootstrap.Modal(
        document.getElementById("ayatDetailModal")
    );
    const ayatDetailContent = document.getElementById("ayat-detail-content");
    const formEvaluasi = document.getElementById("form-evaluasi");
    const inputQueryText = document.getElementById("input-query-text");

    // Variabel untuk load more dan pagination
    let selectedQueryId = null;
    let allAyatData = []; // Semua data ayat untuk load more
    let currentAyatIndex = 0; // Index ayat yang sudah dimuat
    let ayatLoadLimit = 10; // Jumlah ayat per load
    let currentFoundVersesPage = 1; // Halaman saat ini untuk ayat hasil
    let foundVersesPerPage = 20; // Jumlah ayat per halaman
    let currentFoundVerses = []; // Data ayat hasil saat ini
    let groundTruthVerses = []; // Variabel global untuk ayat relevan

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
                    // Update timestamp untuk tracking perubahan
                    localStorage.setItem('lastQueryUpdate', Date.now());
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
          }"><i class="fas fa-trash"></i></button>
        </div>
      </li>`;
        });
        html += "</ul>";
        queryList.innerHTML = html;
        // Event pilih query
        document
            .querySelectorAll("#query-list .list-group-item")
            .forEach((el) => {
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
                    // Reset hasil evaluasi
                    resetRelevantVersesBtn.classList.remove("d-none");
                    resetRelevantVersesBtn.setAttribute(
                        "data-id",
                        selectedQueryId
                    );
                    evaluasiResult.innerHTML = "";
                    // Tampilkan form evaluasi
                    formEvaluasi.classList.remove("d-none");
                    // Autoisi query_text jika ada di list
                    const q = queries.find((q) => q.id === selectedQueryId);
                    if (q) {
                        inputQueryText.value = q.text;
                        inputQueryText.dataset.queryId = q.id; // Set data-query-id agar JS import excel bisa ambil ID
                    }
                });
            });
        // Event hapus query
        document.querySelectorAll(".btn-delete-query").forEach((btn) => {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                const id = this.getAttribute("data-id");
                if (confirm("Hapus query ini?")) {
                    fetch(`/api/query/${id}`, { method: "DELETE" })
                        .then((res) => res.json())
                        .then(() => loadQueries());
                }
            });
        });
    }

    function loadRelevantVerses(queryId) {
        fetch(`/api/query/${queryId}/relevant_verses`)
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    // Simpan ayat relevan ke variable global
                    groundTruthVerses = data.data.map((v) => v.verse_ref);
                    renderRelevantVerses(data.data);
                    document.getElementById("ayat-count").textContent =
                        data.data.length;
                }
            });
    }

    function renderRelevantVerses(verses) {
        // Sederhanakan tampilan jika data banyak
        let html = "";
        if (verses.length === 0) {
            html = '<span class="text-muted">Belum ada ayat relevan.</span>';
        } else if (verses.length <= 100) {
            verses.forEach((v) => {
                html += `<span class="badge bg-primary me-1 mb-1 badge-ayat-ref" data-ref="${v.verse_ref}" style="cursor:pointer">${v.verse_ref}</span>`;
            });
        } else {
            // Tampilkan hanya 10 badge pertama, lalu badge ringkasan
            for (let i = 0; i < 10; i++) {
                html += `<span class="badge bg-primary me-1 mb-1 badge-ayat-ref" data-ref="${verses[i].verse_ref}" style="cursor:pointer">${verses[i].verse_ref}</span>`;
            }
            const sisa = verses.length - 10;
            html += `<span class="badge bg-secondary me-1 mb-1 badge-ayat-more" style="cursor:pointer">... dan ${sisa} ayat lain</span>`;
        }
        relevantVerseList.innerHTML = html;
        // Event listener badge ayat
        relevantVerseList
            .querySelectorAll(".badge-ayat-ref")
            .forEach((badge) => {
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
        // Event listener badge more
        const badgeMore = relevantVerseList.querySelector(".badge-ayat-more");
        if (badgeMore) {
            badgeMore.addEventListener("click", function (e) {
                e.stopPropagation();
                if (selectedQueryId) {
                    showAllAyatDetailModal(selectedQueryId);
                }
            });
        }
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

    // Select All functionality per kolom (toggle)
    document.querySelectorAll(".select-all-methods").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const group = btn.getAttribute("data-group");
            const checkboxes = document.querySelectorAll(
                '.eval-method[data-group="' + group + '"]'
            );
            const allChecked = Array.from(checkboxes).every((cb) => cb.checked);
            checkboxes.forEach(function (cb) {
                cb.checked = !allChecked;
            });
            btn.innerHTML = allChecked ? '<i class="fas fa-square me-1"></i>Unselect All' : '<i class="fas fa-check-square me-1"></i>Select All';
        });
        // Inisialisasi teks tombol sesuai kondisi awal
        const group = btn.getAttribute("data-group");
        const checkboxes = document.querySelectorAll(
            '.eval-method[data-group="' + group + '"]'
        );
        const allChecked = Array.from(checkboxes).every((cb) => cb.checked);
        btn.innerHTML = allChecked ? '<i class="fas fa-square me-1"></i>Unselect All' : '<i class="fas fa-check-square me-1"></i>Select All';
    });
    // Update teks tombol jika ada perubahan manual pada checkbox
    document.querySelectorAll(".eval-method").forEach(function (cb) {
        cb.addEventListener("change", function () {
            const group = cb.getAttribute("data-group");
            const btn = document.querySelector(
                '.select-all-methods[data-group="' + group + '"]'
            );
            if (btn) {
                const checkboxes = document.querySelectorAll(
                    '.eval-method[data-group="' + group + '"]'
                );
                const allChecked = Array.from(checkboxes).every(
                    (cb) => cb.checked
                );
                btn.innerHTML = allChecked ? '<i class="fas fa-square me-1"></i>Unselect All' : '<i class="fas fa-check-square me-1"></i>Select All';
            }
        });
    });

    formEvaluasi.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!selectedQueryId) return;
        const query_text = inputQueryText.value.trim();

        // Ambil metode yang dipilih (VERSI 2 - TANPA ONTOLOGI)
        const selectedMethods = Array.from(
            document.querySelectorAll(".eval-method:checked")
        )
            .map((cb) => cb.value)
            .filter((v) => v !== "synonym"); // Pastikan sinonim tidak pernah dikirim

        if (!query_text) {
            alert("Query evaluasi wajib diisi!");
            return;
        }
        if (selectedMethods.length === 0) {
            alert("Pilih minimal satu metode evaluasi!");
            return;
        }
        showSpinner(evaluasiResult, "Menjalankan evaluasi...");

        // Ambil pengaturan threshold per model dari API
        fetch("/api/models/default_settings")
            .then((res) => res.json())
            .then((settingsData) => {
                if (settingsData.success) {
                    const settings = settingsData.data;
                    const result_limit = 0; // Selalu tak terbatas
                    const thresholds = settings.thresholds || {};
                    // Kirim threshold per model ke backend
                    const threshold_per_model = {};
                    [
                        "word2vec",
                        "fasttext",
                        "glove",
                        "ensemble",
                        // TIDAK ADA ONTOLOGI DI VERSI 2
                    ].forEach((model) => {
                        threshold_per_model[model] =
                            thresholds[model] !== undefined
                                ? thresholds[model]
                                : 0.5;
                    });
                    // GUNAKAN ENDPOINT VERSI 2
                    return fetch(`/api/evaluation-v2/${selectedQueryId}/run`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            query_text,
                            result_limit,
                            threshold_per_model,
                            selected_methods: selectedMethods,
                        }),
                    });
                } else {
                    // Fallback ke nilai default jika gagal ambil settings
                    return fetch(`/api/evaluation-v2/${selectedQueryId}/run`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            query_text,
                            result_limit: 10,
                            threshold_per_model: {
                                word2vec: 0.5,
                                fasttext: 0.5,
                                glove: 0.5,
                                ensemble: 0.5,
                                // TIDAK ADA ONTOLOGI
                            },
                            selected_methods: selectedMethods,
                        }),
                    });
                }
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.success) {
                    renderEvaluationResults(data.results, data.query_text || query_text);
                } else {
                    evaluasiResult.innerHTML = `<div class='alert alert-danger'>${data.message}</div>`;
                }
            })
            .catch(() => {
                evaluasiResult.innerHTML = `<div class='alert alert-danger'>Terjadi kesalahan saat evaluasi.</div>`;
            });
    });

    function renderEvaluationResults(results, queryText) {
        // Hitung summary untuk VERSI 2 (tanpa ontologi)
        let bestIdx = -1;
        let bestF1 = -1;
        let sumPrecision = 0,
            sumRecall = 0,
            sumF1 = 0,
            count = 0;

        results.forEach((r, idx) => {
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

        let avgPrecision = count
            ? (sumPrecision / count).toFixed(3)
            : "-";
        let avgRecall = count
            ? (sumRecall / count).toFixed(3)
            : "-";
        let avgF1 = count ? (sumF1 / count).toFixed(3) : "-";
        let bestLabel =
            bestIdx >= 0 ? results[bestIdx].label : "-";
        let bestF1Str = bestF1 >= 0 ? bestF1.toFixed(3) : "-";

        // Summary HTML untuk VERSI 2
        let summaryHtml = `<div class='mb-3 p-3 bg-light border rounded' id='eval-summary'>
            <h6 class='text-primary mb-2'><i class='fas fa-trophy me-2'></i>Evaluasi Versi 2 - Tanpa Ontologi</h6>
            <div class='row'>
                <div class='col-md-8'>
                    <strong>Query:</strong> "${queryText}"<br>
                    <strong>Metode terbaik:</strong> ${bestLabel} (F1: ${bestF1Str})<br>
                    <strong>Rata-rata:</strong> Precision: ${avgPrecision} | Recall: ${avgRecall} | F1: ${avgF1}
                </div>
                <div class='col-md-4 text-center'>
                    <div class='badge bg-success fs-6 p-2'>${count} model dievaluasi</div>
                </div>
            </div>
        </div>`;

        // Tabel hasil untuk VERSI 2
        let html =
            '<div class="table-responsive"><table class="table table-bordered table-sm"><thead class="table-primary"><tr>' +
            "<th>Model</th><th>TP</th><th>FP</th><th>FN</th><th>Precision</th><th>Recall</th><th>F1-Score</th><th>Execution Time</th><th>Total Found</th><th>Actions</th></tr></thead><tbody>";
        results.forEach((r, idx) => {
            if (r.error) {
                html += `<tr><td colspan='10' class='text-danger'><i class='fas fa-exclamation-triangle me-1'></i>${r.label}: ${r.error}</td></tr>`;
            } else {
                let highlight =
                    idx === bestIdx ? "table-warning fw-bold" : "";
                html +=
                    `<tr class='${highlight}'><td>${r.label}</td><td>${r.true_positive}</td><td>${r.false_positive}</td><td>${r.false_negative}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td><td>${r.exec_time}s</td><td>${r.total_found}</td>` +
                    `<td><button class='btn btn-sm btn-info btn-show-found-verses' data-idx='${idx}'><i class='fas fa-eye me-1'></i>Lihat</button></td></tr>`;
            }
        });
        html += "</tbody></table></div>";
        evaluasiResult.innerHTML = summaryHtml + html;

        // Event listener tombol lihat ayat hasil
        document
            .querySelectorAll(".btn-show-found-verses")
            .forEach((btn) => {
                btn.addEventListener("click", function () {
                    const idx = this.getAttribute("data-idx");
                    const found =
                        results[idx].found_verses || [];
                    showFoundVersesWithPagination(
                        found,
                        groundTruthVerses
                    );
                });
            });
    }

    function showFoundVersesWithPagination(foundVerses, groundTruth = []) {
        currentFoundVerses = foundVerses;
        currentFoundVersesPage = 1;

        // Pisahkan TP dan FP
        let tpVerses = [];
        let fpVerses = [];
        foundVerses.forEach((ref) => {
            if (groundTruth.includes && groundTruth.includes(ref)) {
                tpVerses.push(ref);
            } else {
                fpVerses.push(ref);
            }
        });

        // Gabungkan: TP dulu, lalu FP
        let orderedVerses = tpVerses.concat(fpVerses);
        const totalPages = Math.ceil(orderedVerses.length / foundVersesPerPage);
        const startIndex = (currentFoundVersesPage - 1) * foundVersesPerPage;
        const endIndex = startIndex + foundVersesPerPage;
        const pageVerses = orderedVerses.slice(startIndex, endIndex);

        let content = "";
        if (orderedVerses.length === 0) {
            content = '<div class="text-muted">Tidak ada ayat ditemukan.</div>';
        } else {
            content = '<div class="list-group">';
            pageVerses.forEach((ref) => {
                let isTP = groundTruth.includes
                    ? groundTruth.includes(ref)
                    : false;
                let badgeLabel = isTP ? "TP" : "FP";
                // Ambil detail ayat (arab dan terjemahan) secara async
                content += `<div class='list-group-item' style='margin-bottom:4px;'>`;
                content += `<div><strong>${ref} <span class='badge ${
                    isTP ? "bg-success" : "bg-secondary"
                } ms-2'>${badgeLabel}</span></strong></div>`;
                content += `<div class='ayat-detail-loading' data-ref='${ref}'>Memuat detail ayat...</div>`;
                content += `</div>`;
            });
            content += "</div>";
        }
        const modalBody = document.getElementById("found-verses-content");
        modalBody.innerHTML = content;

        // Debug: Log untuk memastikan konten dimuat
        console.log("Modal content populated:", content.substring(0, 200) + "...");
        console.log("Total verses:", orderedVerses.length, "Page verses:", pageVerses.length);

        // Setelah render, fetch detail ayat untuk setiap baris
        pageVerses.forEach((ref) => {
            const [surah, ayat] = ref.split(":");
            fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`)
                .then((res) => res.json())
                .then((data) => {
                    if (data.success && data.ayat) {
                        const a = data.ayat;
                        const el = modalBody.querySelector(
                            `.ayat-detail-loading[data-ref='${ref}']`
                        );
                        if (el) {
                            el.innerHTML = `<div class='text-arab' style='font-size:1.2em'>${
                                a.text
                            }</div><div><em>${a.translation || ""}</em></div>`;
                        }
                    }
                });
        });

        // Update pagination
        document.getElementById("current-page").textContent =
            currentFoundVersesPage;
        document.getElementById("total-pages").textContent = totalPages;

        // Tampilkan/sembunyikan pagination
        const pagination = document.getElementById("found-verses-pagination");
        if (totalPages > 1) {
            pagination.classList.remove("d-none");
            document.getElementById("prev-page-btn").disabled =
                currentFoundVersesPage === 1;
            document.getElementById("next-page-btn").disabled =
                currentFoundVersesPage === totalPages;
        } else {
            pagination.classList.add("d-none");
        }

        // Tampilkan modal setelah konten diisi
        const modalElement = document.getElementById("modalFoundVerses");
        if (modalElement) {
            try {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log("Modal shown successfully");
            } catch (error) {
                console.error("Error showing modal:", error);
                // Fallback: Show modal using jQuery if Bootstrap modal fails
                if (typeof $ !== 'undefined') {
                    $(modalElement).modal('show');
                } else {
                    // Last resort: Show modal by adding show class
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                    document.body.classList.add('modal-open');
                }
            }
        } else {
            console.error("Modal element not found!");
        }
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
                        const logDate = new Date(l.changed_at).toLocaleString(
                            "id-ID"
                        );
                        html += `<tr><td>${logDate}</td><td>${
                            l.model
                        }</td><td>${l.old_score || "-"}</td><td>${
                            l.new_score
                        }</td></tr>`;
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

    // Event tombol Detail Ayat Relevan
    evaluasiBtn.addEventListener("click", function () {
        if (selectedQueryId) {
            showAllAyatDetailModal(selectedQueryId);
        }
    });

    // Export hasil evaluasi ke Excel
    document
        .getElementById("export-evaluasi-btn")
        .addEventListener("click", function () {
            // Cari tabel hasil evaluasi
            const table = document.querySelector("#eval-summary + table");
            if (!table) {
                Swal.fire({
                    icon: "warning",
                    title: "Tidak ada data",
                    text: "Hasil evaluasi belum tersedia untuk diekspor.",
                });
                return;
            }
            // Konversi tabel ke workbook XLSX
            const wb = XLSX.utils.table_to_book(table, { sheet: "Evaluasi_V2" });
            XLSX.writeFile(wb, "hasil_evaluasi_v2.xlsx");
        });

    // Modal functions (sama seperti versi 1)
    async function showAllAyatDetailModal(queryId) {
        showSpinner(ayatDetailContent, "Memuat detail ayat...");
        // Reset variabel load more
        currentAyatIndex = 0;

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

        // Simpan semua data ayat
        allAyatData = data.data;

        // Update counter
        document.getElementById("total-count").textContent = allAyatData.length;
        document.getElementById("loaded-count").textContent = "0";

        // Buat container list
        let html = '<ul class="list-group mb-3">';
        html += "</ul>";
        ayatDetailContent.innerHTML = html;

        ayatDetailModal.show();

        // Load batch pertama
        await loadMoreAyat();
    }

    async function loadMoreAyat() {
        const container = document.querySelector("#ayat-detail-content ul");
        if (!container) return;

        const loadMoreBtn = document.getElementById("load-more-btn");
        const loadMoreText = document.getElementById("load-more-text");
        const loadMoreSpinner = document.getElementById("load-more-spinner");

        // Set loading state
        loadMoreBtn.disabled = true;
        loadMoreText.classList.add("d-none");
        loadMoreSpinner.classList.remove("d-none");

        const endIndex = Math.min(currentAyatIndex + ayatLoadLimit, allAyatData.length);

        for (let i = currentAyatIndex; i < endIndex; i++) {
            const v = allAyatData[i];
            const [surah, ayat] = v.verse_ref.split(":");

            try {
                const res = await fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`);
                const data = await res.json();

                let itemHtml = `<li class='list-group-item d-flex justify-content-between align-items-center' data-id='${v.id}'>`;
                if (data.success && data.ayat) {
                    const a = data.ayat;
                    itemHtml += `
                        <div>
                            <div><strong>${v.verse_ref}</strong></div>
                            <div class='text-arab small' style='font-size:1em'>${a.text}</div>
                            <div class='text-muted small'><em>${a.translation || ""}</em></div>
                        </div>`;
                } else {
                    itemHtml += `
                        <div>
                            <div><strong>${v.verse_ref}</strong></div>
                            <div class='text-danger small'>Detail ayat tidak ditemukan</div>
                        </div>`;
                }
                itemHtml += `
                    <button class='btn btn-sm btn-danger btn-delete-verse-modal' data-id='${v.id}'>
                        <i class='fas fa-trash'></i>
                    </button>
                </li>`;

                container.insertAdjacentHTML("beforeend", itemHtml);
            } catch (error) {
                let itemHtml = `<li class='list-group-item d-flex justify-content-between align-items-center' data-id='${v.id}'>`;
                itemHtml += `
                    <div>
                        <div><strong>${v.verse_ref}</strong></div>
                        <div class='text-danger small'>Gagal memuat detail</div>
                    </div>
                    <button class='btn btn-sm btn-danger btn-delete-verse-modal' data-id='${v.id}'>
                        <i class='fas fa-trash'></i>
                    </button>
                </li>`;
                container.insertAdjacentHTML("beforeend", itemHtml);
            }
        }

        currentAyatIndex = endIndex;
        document.getElementById("loaded-count").textContent = currentAyatIndex;

        // Update load more button
        if (currentAyatIndex >= allAyatData.length) {
            document
                .getElementById("load-more-container")
                .classList.add("d-none");
        } else {
            document
                .getElementById("load-more-container")
                .classList.remove("d-none");
        }

        // Reset tombol
        loadMoreBtn.disabled = false;
        loadMoreText.classList.remove("d-none");
        loadMoreSpinner.classList.add("d-none");

        // Event hapus ayat di modal
        document.querySelectorAll(".btn-delete-verse-modal").forEach((btn) => {
            btn.addEventListener("click", function () {
                const id = this.getAttribute("data-id");
                showSpinner(ayatDetailContent, "Menghapus ayat...");
                fetch(`/api/query/relevant_verse/${id}`, { method: "DELETE" })
                    .then((res) => res.json())
                    .then(() => showAllAyatDetailModal(selectedQueryId));
            });
        });
    }

    // Form tambah ayat di modal
    document
        .getElementById("form-add-verse-modal")
        .addEventListener("submit", function (e) {
            e.preventDefault();
            const verse = document
                .getElementById("verse-ref-modal")
                .value.trim();
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

    // Event listener untuk load more
    document
        .getElementById("load-more-btn")
        .addEventListener("click", loadMoreAyat);

    // Pagination untuk found verses (sama seperti versi 1)
    document
        .getElementById("prev-page-btn")
        .addEventListener("click", function () {
            if (currentFoundVersesPage > 1) {
                currentFoundVersesPage--;
                showFoundVersesWithPagination(currentFoundVerses);
            }
        });

    document
        .getElementById("next-page-btn")
        .addEventListener("click", function () {
            const totalPages = Math.ceil(
                currentFoundVerses.length / foundVersesPerPage
            );
            if (currentFoundVersesPage < totalPages) {
                currentFoundVersesPage++;
                showFoundVersesWithPagination(currentFoundVerses);
            }
        });

    // Auto-refresh query list jika ada perubahan dari halaman lain
    // setInterval(() => {
    //     const lastUpdate = localStorage.getItem('lastQueryUpdate');
    //     if (lastUpdate && (!window.lastQueryCheck || parseInt(lastUpdate) > window.lastQueryCheck)) {
    //         window.lastQueryCheck = parseInt(lastUpdate);
    //         loadQueries(); // Reload query list jika ada perubahan
    //     }
    // }, 2000); // Check setiap 2 detik

    loadQueries();
});
