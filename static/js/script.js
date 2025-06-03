/**
 * Script kustom untuk Mesin Pencarian Semantik Al-Quran
 */

document.addEventListener("DOMContentLoaded", function () {
  // Inisialisasi komponen
  initializeTooltips();
  setupFormValidation();
  setupSearchInteractions();

  // Animasi untuk hasil pencarian
  setupResultAnimations();

  // Muat model yang tersedia
  loadAvailableModels();
});

/**
 * Inisialisasi tooltips Bootstrap
 */
function initializeTooltips() {
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

/**
 * Setup validasi form
 */
function setupFormValidation() {
  // Validasi pada form submit
  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", function (event) {
      if (!searchForm.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      searchForm.classList.add("was-validated");
    });
  }
}

/**
 * Setup interaksi pencarian
 */
function setupSearchInteractions() {
  // Update slider value
  const similaritySlider = document.getElementById("similarityThreshold");
  const thresholdValue = document.getElementById("thresholdValue");

  if (similaritySlider && thresholdValue) {
    similaritySlider.addEventListener("input", function () {
      thresholdValue.textContent = this.value;
    });
  }

  // Reset button functionality
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      const searchForm = document.getElementById("searchForm");
      searchForm.reset();

      // Reset threshold display
      if (thresholdValue) {
        thresholdValue.textContent = "0.5";
      }

      // Hide results card
      const resultsCard = document.getElementById("resultsCard");
      if (resultsCard) {
        resultsCard.classList.add("d-none");
      }
    });
  }

  // Handle form submission
  const searchForm = document.getElementById("searchForm");
  if (searchForm) {
    searchForm.addEventListener("submit", function (event) {
      event.preventDefault();

      // Tampilkan loading state
      showLoading(true);
      // Ambil nilai form
      const searchQuery = document.getElementById("searchQuery")?.value || "";
      const modelType =
        document.getElementById("modelType")?.value || "word2vec";
      const resultCount = parseInt(
        document.getElementById("resultCount")?.value || "10"
      );
      const threshold = 0.5; // Default threshold value

      // Buat objek data
      const searchData = {
        query: searchQuery,
        model: modelType,
        language: langSelect,
        limit: resultCount,
        threshold: threshold,
      };

      // Kirim request ke API
      fetch("/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(searchData),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              "Network response was not ok: " + response.statusText
            );
          }
          return response.json();
        })
        .then((data) => {
          // Tampilkan hasil pencarian
          displaySearchResults(data);

          // Sembunyikan loading state
          showLoading(false);
        })
        .catch((error) => {
          console.error("Error:", error);
          // Tampilkan pesan error
          displayError("Terjadi kesalahan saat mencari: " + error.message);

          // Sembunyikan loading state
          showLoading(false);
        });
    });
  }
}

/**
 * Menampilkan pesan error
 */
function displayError(message) {
  const searchResults = document.getElementById("searchResults");
  const resultsCard = document.getElementById("resultsCard");

  if (!searchResults || !resultsCard) return;

  // Bersihkan hasil sebelumnya
  searchResults.innerHTML = "";

  // Tampilkan pesan error
  const errorHtml = `
        <div class="list-group-item p-3">
            <div class="alert alert-danger mb-0">
                <i class="fas fa-exclamation-circle me-2"></i> ${message}
            </div>
        </div>
    `;
  searchResults.innerHTML = errorHtml;

  // Tampilkan kartu hasil
  resultsCard.classList.remove("d-none");
}

/**
 * Tampilkan loading state
 */
function showLoading(isLoading) {
  const searchButton = document.querySelector(
    '#searchForm button[type="submit"]'
  );

  if (searchButton) {
    if (isLoading) {
      searchButton.innerHTML =
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Mencari...';
      searchButton.disabled = true;
    } else {
      searchButton.innerHTML = '<i class="fas fa-search me-1"></i> Cari';
      searchButton.disabled = false;
    }
  }
}

/**
 * Tampilkan hasil pencarian
 */
function displaySearchResults(data) {
  const searchResults = document.getElementById("searchResults");
  const resultsCard = document.getElementById("resultsCard");

  if (!searchResults || !resultsCard) return;

  // Bersihkan hasil sebelumnya
  searchResults.innerHTML = "";

  // Header untuk hasil
  const resultsHeader = document.querySelector("#resultsCard .card-header h5");
  if (resultsHeader) {
    resultsHeader.textContent = `Hasil Pencarian untuk "${data.query}" menggunakan ${data.model}`;
  }

  // Tampilkan hasil
  if (data.results && data.results.length > 0) {
    data.results.forEach((result, index) => {
      const resultItem = document.createElement("div");
      resultItem.className = "list-group-item p-3 animate-fade-in";
      resultItem.style.animationDelay = `${index * 100}ms`;

      resultItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between mb-2">
                    <h5 class="mb-1">${result.surah_name} (${
        result.surah_number
      }): ${result.ayat_number}</h5>
                    <span class="badge bg-success">${(
                      result.similarity * 100
                    ).toFixed(1)}% kecocokan</span>
                </div>
                <p class="arabic-text text-end mb-2" dir="rtl">${
                  result.arabic
                }</p>
                <p class="mb-0">${result.translation}</p>
            `;

      searchResults.appendChild(resultItem);
    });
  } else {
    // Tampilkan pesan jika tidak ada hasil
    searchResults.innerHTML = `
            <div class="list-group-item p-3">
                <div class="alert alert-info mb-0">
                    <i class="fas fa-info-circle me-2"></i> Tidak ditemukan hasil yang sesuai dengan pencarian Anda.
                </div>
            </div>
        `;
  }

  // Tampilkan kartu hasil
  resultsCard.classList.remove("d-none");

  // Scroll ke hasil
  resultsCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Muat model yang tersedia dari API
 */
function loadAvailableModels() {
  const modelSelect = document.getElementById("modelSelect");
  if (!modelSelect) return;

  fetch("/api/models")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((models) => {
      // Bersihkan pilihan yang ada
      modelSelect.innerHTML = "";

      // Tambahkan pilihan model
      models.forEach((model) => {
        const option = document.createElement("option");
        option.value = model.id;
        option.textContent = model.name;
        option.title = model.description;
        modelSelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error loading models:", error);
    });
}

/**
 * Setup animasi untuk hasil pencarian
 */
function setupResultAnimations() {
  // Implementasi animasi tampilan hasil
  document.addEventListener("scroll", function () {
    const animateElements = document.querySelectorAll(
      ".animate-on-scroll:not(.animated)"
    );

    animateElements.forEach((element) => {
      if (isElementInViewport(element)) {
        element.classList.add("animated", "animate-fade-in");
      }
    });
  });
}

/**
 * Cek apakah elemen dalam viewport
 */
function isElementInViewport(el) {
  const rect = el.getBoundingClientRect();

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Menampilkan distribusi hasil pencarian
 */
function showSearchDistribution() {
  const searchResults = currentSearchResults;

  if (!searchResults || searchResults.length === 0) {
    showToast("Tidak ada hasil pencarian untuk divisualisasikan", "warning");
    return;
  }

  // Tampilkan modal
  const distributionModal = new bootstrap.Modal(
    document.getElementById("searchDistributionModal")
  );
  distributionModal.show();

  // Tampilkan loading state
  document.getElementById("distributionChartContainer").innerHTML =
    '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Memuat distribusi...</p></div>';
  document.getElementById("distributionTableBody").innerHTML = "";

  // Kirim data ke API untuk mendapatkan distribusi
  fetch("/api/search/distribution", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ results: searchResults }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success && data.data) {
        renderDistributionChart(data.data);
        renderDistributionTable(data.data);
      } else {
        document.getElementById("distributionChartContainer").innerHTML =
          '<div class="alert alert-info">Tidak ada informasi klasifikasi yang tersedia untuk hasil pencarian ini</div>';
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("distributionChartContainer").innerHTML =
        '<div class="alert alert-danger">Terjadi kesalahan saat memuat distribusi</div>';
    });
}

/**
 * Render chart distribusi hasil pencarian
 */
function renderDistributionChart(distribution) {
  // Hapus chart sebelumnya jika ada
  if (window.distributionChart) {
    window.distributionChart.destroy();
  }

  const chartContainer = document.getElementById("distributionChartContainer");
  chartContainer.innerHTML = '<canvas id="distributionChart"></canvas>';

  const canvas = document.getElementById("distributionChart");
  const ctx = canvas.getContext("2d");

  // Persiapkan data untuk chart
  const labels = distribution.map((item) => item.category);
  const counts = distribution.map((item) => item.count);

  // Buat warna untuk chart berdasarkan jumlah kategori
  const backgroundColors = generateChartColors(distribution.length);

  // Buat chart baru
  window.distributionChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          data: counts,
          backgroundColor: backgroundColors,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: {
            boxWidth: 12,
            font: {
              size: 11,
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const value = context.raw;
              const total = context.dataset.data.reduce(
                (acc, val) => acc + val,
                0
              );
              const percentage = ((value / total) * 100).toFixed(1);
              return `${context.label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

/**
 * Render tabel distribusi hasil pencarian
 */
function renderDistributionTable(distribution) {
  const tableBody = document.getElementById("distributionTableBody");
  tableBody.innerHTML = "";

  // Hitung total
  const total = distribution.reduce((sum, item) => sum + item.count, 0);

  // Tambahkan setiap kategori ke tabel
  distribution.forEach((item, index) => {
    const percentage = ((item.count / total) * 100).toFixed(1);
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${index + 1}</td>
            <td>${item.category}</td>
            <td class="text-center">${item.count}</td>
            <td class="text-center">${percentage}%</td>
        `;

    tableBody.appendChild(row);
  });

  // Tambahkan baris total
  const totalRow = document.createElement("tr");
  totalRow.className = "table-active fw-bold";
  totalRow.innerHTML = `
        <td colspan="2">Total</td>
        <td class="text-center">${total}</td>
        <td class="text-center">100%</td>
    `;
  tableBody.appendChild(totalRow);
}

/**
 * Menghasilkan warna untuk chart
 */
function generateChartColors(count) {
  const colors = [];
  const baseColors = [
    "rgba(54, 162, 235, 0.8)",
    "rgba(255, 99, 132, 0.8)",
    "rgba(255, 206, 86, 0.8)",
    "rgba(75, 192, 192, 0.8)",
    "rgba(153, 102, 255, 0.8)",
    "rgba(255, 159, 64, 0.8)",
    "rgba(199, 199, 199, 0.8)",
    "rgba(83, 102, 255, 0.8)",
    "rgba(40, 159, 150, 0.8)",
    "rgba(210, 105, 30, 0.8)",
  ];

  for (let i = 0; i < count; i++) {
    if (i < baseColors.length) {
      colors.push(baseColors[i]);
    } else {
      // Jika lebih dari jumlah warna dasar, generate secara random
      const r = Math.floor(Math.random() * 255);
      const g = Math.floor(Math.random() * 255);
      const b = Math.floor(Math.random() * 255);
      colors.push(`rgba(${r}, ${g}, ${b}, 0.8)`);
    }
  }

  return colors;
}
