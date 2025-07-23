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
        ayatData = [];
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
        ayatData.sort((a, b) => {
            const [surahA, ayatA] = a.split(":").map(Number);
            const [surahB, ayatB] = b.split(":").map(Number);
            if (surahA !== surahB) return surahA - surahB;
            return ayatA - ayatB;
        });
        if (ayatData.length === 0) {
            importAyatError.classList.remove("d-none");
            importAyatError.innerText =
                "Sheet tidak mengandung data ayat dengan format surah_id:ayat_id pada hirarki terakhir.";
            previewAyatGroup.classList.add("d-none");
            submitImportBtn.classList.add("d-none");
        } else {
            importAyatError.classList.add("d-none");
            importAyatError.innerText = "";
            previewAyatGroup.classList.remove("d-none");
            // Tampilkan jumlah data dan preview urut
            previewAyatExcel.innerHTML =
                `<div class='mb-2 fw-bold'>Jumlah data: ${ayatData.length}</div>` +
                ayatData.map((a) => `<div>${a}</div>`).join("");
            submitImportBtn.classList.remove("d-none");
        }
    });

    function extractAyatFromSheet(json) {
        // Ambil semua data yang mengandung format 'Qs.' di seluruh sheet, hilangkan duplikat
        let ayatSet = new Set();
        json.forEach((row) => {
            row.forEach((cell) => {
                if (
                    typeof cell === "string" &&
                    /^Qs\.\d{1,3}:\d{1,3}$/.test(cell.trim())
                ) {
                    // Hilangkan 'Qs.'
                    ayatSet.add(cell.trim().replace(/^Qs\./, ""));
                }
            });
        });
        return Array.from(ayatSet);
    }

    document
        .getElementById("formImportAyatExcel")
        .addEventListener("submit", function (e) {
            e.preventDefault();
            if (ayatData.length === 0) return;
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
            fetch("/api/query/import-ayat-excel", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ayat: ayatData, query_id: queryId }),
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.success) {
                        modalImport.hide();
                        location.reload();
                    } else {
                        importAyatError.classList.remove("d-none");
                        importAyatError.innerText =
                            data.message || "Gagal import data ayat.";
                    }
                })
                .catch(() => {
                    importAyatError.classList.remove("d-none");
                    importAyatError.innerText =
                        "Terjadi kesalahan saat import.";
                })
                .finally(() => {
                    submitImportBtn.disabled = false;
                });
        });
});
