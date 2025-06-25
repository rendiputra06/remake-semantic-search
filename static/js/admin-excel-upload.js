/**
 * Excel upload functionality for admin panel
 */
function showExcelUploadModal() {
  // Reset form
  document.getElementById("excelUploadForm").reset();
  document.getElementById("sheet-name").innerHTML =
    '<option value="">Pilih file terlebih dahulu</option>';
  document.getElementById("sheet-name").disabled = true;
  document.getElementById("upload-progress-container").classList.add("d-none");
  document.getElementById("upload-progress-bar").style.width = "0%";
  document.getElementById("preview-container").classList.add("d-none");

  // Load daftar indeks root untuk parent
  fetch("/api/quran-index/roots")
    .then((response) => response.json())
    .then((result) => {
      if (result.success) {
        const parentSelect = document.getElementById("parent-index");
        let options = '<option value="">Root (Tidak ada parent)</option>';

        result.data.forEach((index) => {
          options += `<option value="${index.id}">${index.title} (Level ${index.level})</option>`;
        });

        parentSelect.innerHTML = options;
      }
    })
    .catch((error) => {
      console.error("Error fetching root indexes:", error);
      showAlert("danger", "Gagal memuat daftar indeks utama");
    });

  // Event listener for file input
  document
    .getElementById("excel-file")
    .addEventListener("change", handleFileSelect);

  // Show modal
  const modal = new bootstrap.Modal(
    document.getElementById("excelUploadModal")
  );
  modal.show();

  // Event handler for upload button
  document.getElementById("upload-excel-btn").onclick = handleUpload;
}

function handleFileSelect() {
  const file = this.files[0];
  if (file) {
    // Validate file type
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      showAlert("danger", "File harus berupa Excel (.xlsx atau .xls)");
      this.value = '';
      return;
    }
    
    // Enable sheet selection
    document.getElementById("sheet-name").disabled = false;
    
    // Get sheet names from Excel file
    const formData = new FormData();
    formData.append("file", file);
    
    fetch("/api/quran-index/excel/sheets", {
      method: "POST",
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(errorData => {
          throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        });
      }
      return response.json();
    })
    .then(result => {
      if (result.success) {
        const sheetSelect = document.getElementById("sheet-name");
        let options = '<option value="">Pilih sheet</option>';
        
        result.data.forEach(sheet => {
          options += `<option value="${sheet}">${sheet}</option>`;
        });
        
        sheetSelect.innerHTML = options;
      } else {
        showAlert("danger", result.message || "Gagal membaca file Excel");
      }
    })
    .catch(error => {
      console.error("Error reading Excel file:", error);
      showAlert("danger", `Terjadi kesalahan saat membaca file Excel: ${error.message}`);
    });
  }
}

function handleUpload() {
  const fileInput = document.getElementById("excel-file");
  const sheetName = document.getElementById("sheet-name").value;
  const parentId = document.getElementById("parent-index").value || null;

  if (!fileInput.files.length) {
    showAlert("danger", "Silakan pilih file Excel terlebih dahulu");
    return;
  }

  if (!sheetName) {
    showAlert("danger", "Silakan pilih sheet yang akan diimpor");
    return;
  }

  // Create FormData
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("sheet_name", sheetName);
  if (parentId) formData.append("parent_id", parentId);

  // Show loading animation
  const progressContainer = document.getElementById(
    "upload-progress-container"
  );
  const progressBar = document.getElementById("upload-progress-bar");
  progressContainer.classList.remove("d-none");
  document.getElementById("processing-text").textContent =
    "Mengimpor data dari Excel...";
  progressBar.style.width = "0%";

  // Disable form elements
  disableFormElements(true);

  // Simulate progress
  simulateProgress();

  // Perform upload
  uploadExcelFile(formData);
}

function disableFormElements(disabled) {
  document.getElementById("upload-excel-btn").disabled = disabled;
  document.getElementById("excel-file").disabled = disabled;
  document.getElementById("sheet-name").disabled = disabled;
  document.getElementById("parent-index").disabled = disabled;
}

function simulateProgress() {
  let width = 0;
  const progressBar = document.getElementById("upload-progress-bar");
  const interval = setInterval(() => {
    if (width >= 90) {
      clearInterval(interval);
    } else {
      width += 5;
      progressBar.style.width = width + "%";
    }
  }, 500);
}

function uploadExcelFile(formData) {
  fetch("/api/quran-index/import-excel", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((result) => {
      if (result.success) {
        showAlert("success", "File Excel berhasil diimpor");
        location.reload();
      } else {
        showAlert("danger", result.message || "Gagal mengimpor file Excel");
        disableFormElements(false);
      }
    })
    .catch((error) => {
      console.error("Error uploading Excel:", error);
      showAlert("danger", "Terjadi kesalahan saat mengimpor file");
      disableFormElements(false);
    });
}

function showAlert(type, message) {
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
