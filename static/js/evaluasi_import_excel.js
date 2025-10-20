// evaluasi_import_excel.js
// Fitur import ayat relevan dari file Excel pada halaman evaluasi
// Pastikan sudah include library xlsx.min.js di template jika belum

document.addEventListener("DOMContentLoaded", function () {
    const importBtn = document.getElementById("import-ayat-excel-btn");
    const modalImport = new bootstrap.Modal(
        document.getElementById("modalImportAyatExcel")
    );
    const inputExcelFile = document.getElementById("inputExcelFile");
    const sheetSelectGroup = document.getElementById("sheetSelectGroup");
    const selectSheet = document.getElementById("selectSheet");
    const previewAyatGroup = document.getElementById("previewAyatGroup");
    const previewAyatExcel = document.getElementById("previewAyatExcel");
    const importAyatError = document.getElementById("importAyatError");
    const submitImportBtn = document.getElementById("submitImportAyatExcel");
    let workbook = null;
    let ayatData = [];

    importBtn.addEventListener("click", function () {
        modalImport.show();
        resetImportModal();
    });

    function resetImportModal() {
        inputExcelFile.value = "";
        sheetSelectGroup.classList.add("d-none");
        selectSheet.innerHTML = "";
        previewAyatGroup.classList.add("d-none");
        previewAyatExcel.innerHTML = "";
        importAyatError.classList.add("d-none");
        importAyatError.innerText = "";
        submitImportBtn.classList.add("d-none");
        ayatData = { verses: [], duplicates: 0, totalFound: 0, validFormat: 0 }; // Reset dengan struktur baru
    }

    inputExcelFile.addEventListener("change", function (e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function (evt) {
            const data = evt.target.result;
            workbook = XLSX.read(data, { type: "binary" });
            // Tampilkan sheet
            selectSheet.innerHTML = "";
            workbook.SheetNames.forEach(function (name, idx) {
                const opt = document.createElement("option");
                opt.value = name;
                opt.text = name;
                selectSheet.appendChild(opt);
            });
            sheetSelectGroup.classList.remove("d-none");
        };
        reader.readAsBinaryString(file);
    });

    selectSheet.addEventListener("change", function () {
        const sheetName = selectSheet.value;
        if (!sheetName) return;
        const sheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(sheet, { header: 1 });
        ayatData = extractAyatFromSheet(json);
        // Urutkan ayatData berdasarkan surah (sebelum preview)
        ayatData.verses.sort((a, b) => {
            const [surahA, ayatA] = a.split(":").map(Number);
            const [surahB, ayatB] = b.split(":").map(Number);
            if (surahA !== surahB) return surahA - surahB;
            return ayatA - ayatB;
        });
        if (ayatData.verses.length === 0) {
            importAyatError.classList.remove("d-none");
            importAyatError.innerText =
                "Sheet tidak mengandung data ayat dengan format surah_id:ayat_id pada hirarki terakhir.";
            previewAyatGroup.classList.add("d-none");
            submitImportBtn.classList.add("d-none");
        } else {
            importAyatError.classList.add("d-none");
            importAyatError.innerText = "";
            previewAyatGroup.classList.remove("d-none");

            // Enhanced preview dengan detailed statistics
            let previewHTML = `<div class='mb-2 fw-bold'>📊 Statistik Data:</div>`;
            previewHTML += `<div class='mb-2 text-muted small'>`;
            previewHTML += `• Data unik yang akan diimport: <strong>${ayatData.verses.length}</strong><br>`;
            if (ayatData.duplicates > 0) {
                previewHTML += `• Duplikasi dalam sheet: <strong class='text-warning'>${ayatData.duplicates}</strong><br>`;
            }
            previewHTML += `• Total cell diperiksa: <strong>${ayatData.totalFound}</strong><br>`;
            previewHTML += `• Format valid ditemukan: <strong>${ayatData.validFormat}</strong>`;
            previewHTML += `</div>`;

            previewHTML += `<div class='mb-2 fw-bold'>📋 Preview Ayat (urut berdasarkan surah):</div>`;
            previewHTML += `<div class='ayat-preview' style='max-height: 200px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 0.25rem; padding: 0.5rem;'>`;
            previewHTML += ayatData.verses.map((a) => `<div class='mb-1'>${a}</div>`).join("");
            previewHTML += `</div>`;

            previewAyatExcel.innerHTML = previewHTML;
            submitImportBtn.classList.remove("d-none");
        }
    });

    function extractAyatFromSheet(json) {
        // Enhanced extraction dengan detailed statistics
        let ayatSet = new Set();
        let duplicatesInSheet = 0;
        let totalCellsChecked = 0;
        let validFormatCount = 0;

        json.forEach((row) => {
            row.forEach((cell) => {
                totalCellsChecked++;
                if (typeof cell === "string") {
                    const trimmedCell = cell.trim();
                    if (/^Qs\.\d{1,3}:\d{1,3}$/.test(trimmedCell)) {
                        validFormatCount++;
                        const cleanRef = trimmedCell.replace(/^Qs\./, "");
                        if (ayatSet.has(cleanRef)) {
                            duplicatesInSheet++;
                        } else {
                            ayatSet.add(cleanRef);
                        }
                    }
                }
            });
        });

        const uniqueAyat = Array.from(ayatSet);

        console.log(`📊 Extraction Stats:
        • Total cells checked: ${totalCellsChecked}
        • Valid format found: ${validFormatCount}
        • Duplicates in sheet: ${duplicatesInSheet}
        • Unique ayat extracted: ${uniqueAyat.length}`);

        return {
            verses: uniqueAyat,
            duplicates: duplicatesInSheet,
            totalFound: totalCellsChecked,
            validFormat: validFormatCount
        };
    }

    document
        .getElementById("formImportAyatExcel")
        .addEventListener("submit", function (e) {
            e.preventDefault();
            if (ayatData.verses.length === 0) return;
            // Ambil query_id dari input-query-text (readonly, value = id atau text)
            let queryId = null;
            const inputQueryText = document.getElementById("input-query-text");
            if (
                inputQueryText &&
                inputQueryText.dataset &&
                inputQueryText.dataset.queryId
            ) {
                queryId = inputQueryText.dataset.queryId;
            } else if (inputQueryText && inputQueryText.value) {
                // Jika value adalah id
                queryId = inputQueryText.value;
            }
            if (!queryId) {
                importAyatError.classList.remove("d-none");
                importAyatError.innerText =
                    "Query belum dipilih atau query_id tidak ditemukan.";
                return;
            }
            submitImportBtn.disabled = true;
            Swal.fire({
                title: "Import data ayat relevan...",
                text: "Mohon tunggu, proses sedang berjalan.",
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                },
            });
            fetch("/api/query/import-ayat-excel", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ayat: ayatData.verses, query_id: queryId }),
            })
                .then((res) => res.json())
                .then((data) => {
                    Swal.close();
                    if (data.success) {
                        modalImport.hide();

                        // Enhanced success message dengan statistics
                        let successMessage = data.message;
                        if (data.statistics) {
                            const stats = data.statistics;
                            successMessage += `\n\n📊 **Detail Import:**\n`;
                            successMessage += `• Ayat baru: ${stats.inserted}\n`;
                            if (stats.duplicates > 0) {
                                successMessage += `• Duplikasi diabaikan: ${stats.duplicates}\n`;
                            }
                            successMessage += `• Total diproses: ${stats.total_processed}`;

                            if (stats.existing_before > 0) {
                                successMessage += `\n• Total relevan sekarang: ${stats.existing_before + stats.inserted}`;
                            }
                        }

                        Swal.fire({
                            icon: 'success',
                            title: 'Import Berhasil!',
                            html: successMessage.replace(/\n/g, '<br>'),
                            confirmButtonText: 'OK'
                        }).then(() => {
                            location.reload();
                        });
                    } else {
                        importAyatError.classList.remove("d-none");
                        importAyatError.innerText =
                            data.message || "Gagal import data ayat.";
                    }
                })
                .catch(() => {
                    Swal.close();
                    importAyatError.classList.remove("d-none");
                    importAyatError.innerText =
                        "Terjadi kesalahan saat import.";
                })
                .finally(() => {
                    submitImportBtn.disabled = false;
                });
        });
});
