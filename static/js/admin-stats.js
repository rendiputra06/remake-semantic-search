/**
 * Statistics functionality for admin panel
 */

function loadStats() {
  fetch("/api/statistics")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Update card statistik
      document.getElementById("total-categories").textContent =
        data.total_categories;
      document.getElementById("total-ayat").textContent = data.total_verses;
      document.getElementById("categories-with-ayat").textContent =
        data.categories_with_ayat;
      document.getElementById("root-categories").textContent =
        data.root_categories;

      // Render statistik level
      renderLevelStats(data.level_stats, data.total_categories);

      // Render statistik surah
      renderSurahStats(data.surah_stats, data.total_verses);

      // Sembunyikan spinner loading
      document.getElementById("stats-loading").style.display = "none";
      document.getElementById("stats-content").classList.remove("d-none");
    })
    .catch((error) => {
      console.error("Error fetching statistics:", error);
      document.getElementById("stats-loading").style.display = "none";
      // Tampilkan pesan error
      showAlert("danger", "Gagal memuat statistik: " + error.message);
    });
}

function renderLevelStats(levelStats, totalCategories) {
  const tbody = document.getElementById("level-stats-tbody");
  tbody.innerHTML = "";

  levelStats.forEach((stat) => {
    const row = document.createElement("tr");
    const level = document.createElement("td");
    level.textContent = `Level ${stat.level}`;

    const count = document.createElement("td");
    count.textContent = stat.count;

    const percentage = document.createElement("td");
    const percentValue = ((stat.count / totalCategories) * 100).toFixed(2);
    percentage.textContent = `${percentValue}%`;

    row.appendChild(level);
    row.appendChild(count);
    row.appendChild(percentage);
    tbody.appendChild(row);
  });
}

function renderSurahStats(surahStats, totalVerses) {
  const tbody = document.getElementById("surah-stats-tbody");
  tbody.innerHTML = "";

  surahStats.forEach((stat) => {
    const row = document.createElement("tr");

    const surah = document.createElement("td");
    surah.textContent = `${stat.surah_number}. ${stat.surah_name}`;

    const count = document.createElement("td");
    count.textContent = stat.verse_count;

    const percentage = document.createElement("td");
    const percentValue = ((stat.verse_count / totalVerses) * 100).toFixed(2);
    percentage.textContent = `${percentValue}%`;

    row.appendChild(surah);
    row.appendChild(count);
    row.appendChild(percentage);
    tbody.appendChild(row);
  });
}

// Add event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Event listener untuk refresh statistik
  const refreshBtn = document.getElementById("refresh-stats-btn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", loadStats);
  }

  // Event listener untuk tab statistik
  const statsTab = document.getElementById("stats-tab");
  if (statsTab) {
    statsTab.addEventListener("shown.bs.tab", function () {
      loadStats();
    });
  }
});
