/**
 * JavaScript untuk halaman pencarian lexical
 */

$(document).ready(function () {
  // Handle form submission
  $("#lexicalSearchForm").submit(function (e) {
    e.preventDefault();
    performLexicalSearch();
  });

  // Handle reset button
  $("#resetBtn").click(function () {
    resetForm();
  });

  // Handle exact match and regex checkboxes
  $("#exactMatch, #useRegex").change(function () {
    // If exact match is checked, uncheck regex
    if (
      $("#exactMatch").is(":checked") &&
      $(this).attr("id") === "exactMatch"
    ) {
      $("#useRegex").prop("checked", false);
    }
    // If regex is checked, uncheck exact match
    if ($("#useRegex").is(":checked") && $(this).attr("id") === "useRegex") {
      $("#exactMatch").prop("checked", false);
    }
  });

  // Check URL parameters for auto-search
  const urlParams = new URLSearchParams(window.location.search);
  const queryParam = urlParams.get("query");
  if (queryParam) {
    $("#query").val(queryParam);
    setTimeout(() => {
      performLexicalSearch();
    }, 500);
  }
});

/**
 * Perform lexical search
 */
function performLexicalSearch() {
  const query = $("#query").val().trim();
  const exactMatch = $("#exactMatch").is(":checked");
  const useRegex = $("#useRegex").is(":checked");
  const limit = $("#limit").val();

  if (!query) {
    showAlert("Masukkan kata kunci pencarian.", "warning");
    return;
  }

  // Show loading state
  showLoading(true);
  hideResults();

  // Prepare request data
  const requestData = {
    query: query,
    exact_match: exactMatch,
    use_regex: useRegex,
    limit: parseInt(limit),
  };

  // Make API call
  $.ajax({
    type: "POST",
    url: "/api/search/search/lexical",
    contentType: "application/json",
    data: JSON.stringify(requestData),
    success: function (response) {
      showLoading(false);

      if (response.success) {
        displayResults(response.data);
      } else {
        showAlert(
          "Error: " + (response.message || "Pencarian gagal"),
          "danger"
        );
      }
    },
    error: function (xhr, status, error) {
      showLoading(false);
      let errorMessage = "Pencarian gagal";

      try {
        const errorResponse = xhr.responseJSON;
        if (errorResponse && errorResponse.message) {
          errorMessage = errorResponse.message;
        }
      } catch (e) {
        console.error("Error parsing error response:", e);
      }

      showAlert("Error: " + errorMessage, "danger");
    },
  });
}

/**
 * Display search results
 */
function displayResults(data) {
  const resultsContainer = $("#searchResults");
  const resultsCard = $("#resultsCard");
  const noResultsCard = $("#noResultsCard");

  // Hide all result containers
  resultsCard.addClass("d-none");
  noResultsCard.addClass("d-none");

  if (!data.results || data.results.length === 0) {
    noResultsCard.removeClass("d-none");
    return;
  }

  let resultsHtml = "";

  // Add search info header
  resultsHtml += `
        <div class="list-group-item bg-light">
            <div class="d-flex justify-content-between align-items-center">
                <span>Ditemukan <strong>${
                  data.results.length
                }</strong> hasil untuk pencarian "${data.query}"</span>
                <div class="small text-muted">
                    ${getSearchTypeLabel(data.exact_match, data.use_regex)}
                </div>
            </div>
        </div>
    `;

  // Display each result
  data.results.forEach((result, index) => {
    const resultClass = index % 2 === 0 ? "bg-light" : "";
    const matchTypeBadge = getMatchTypeBadge(result.match_type);

    resultsHtml += `
            <div class="list-group-item ${resultClass}">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">Surah ${result.surah_number} (${
      result.surah_name
    }), Ayat ${result.ayat_number}</h5>
                    ${matchTypeBadge}
                </div>
                <p class="mb-1 arabic-text text-end">${result.arabic}</p>
                <p class="mb-1">${highlightQuery(
                  result.translation,
                  data.query
                )}</p>
                ${
                  result.classification
                    ? `<div class="small text-muted mt-1">Klasifikasi: ${result.classification.title}</div>`
                    : ""
                }
            </div>
        `;
  });

  resultsContainer.html(resultsHtml);
  resultsCard.removeClass("d-none");

  // Scroll to results
  $("html, body").animate(
    {
      scrollTop: resultsCard.offset().top - 20,
    },
    500
  );
}

/**
 * Get search type label
 */
function getSearchTypeLabel(exactMatch, useRegex) {
  if (useRegex) {
    return '<span class="badge bg-info">Regex Search</span>';
  } else if (exactMatch) {
    return '<span class="badge bg-warning">Exact Phrase</span>';
  } else {
    return '<span class="badge bg-success">Keyword Search</span>';
  }
}

/**
 * Get match type badge
 */
function getMatchTypeBadge(matchType) {
  const badges = {
    exact_phrase: '<span class="badge bg-warning">Frasa Persis</span>',
    regex: '<span class="badge bg-info">Regex</span>',
    keywords: '<span class="badge bg-success">Kata Kunci</span>',
  };

  return badges[matchType] || '<span class="badge bg-secondary">Unknown</span>';
}

/**
 * Highlight query in text
 */
function highlightQuery(text, query) {
  if (!query) return text;

  const regex = new RegExp(
    `(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`,
    "gi"
  );
  return text.replace(regex, '<mark class="bg-warning">$1</mark>');
}

/**
 * Show loading state
 */
function showLoading(show) {
  const loadingSpinner = $("#loadingSpinner");
  const searchBtn = $("#searchBtn");
  const searchBtnText = $("#searchBtnText");

  if (show) {
    loadingSpinner.removeClass("d-none");
    searchBtn.prop("disabled", true);
    searchBtnText.html("Mencari...");
    searchBtn.prepend(
      '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>'
    );
  } else {
    loadingSpinner.addClass("d-none");
    searchBtn.prop("disabled", false);
    searchBtn.find(".spinner-border").remove();
    searchBtnText.html("Cari");
  }
}

/**
 * Hide all result containers
 */
function hideResults() {
  $("#resultsCard").addClass("d-none");
  $("#noResultsCard").addClass("d-none");
}

/**
 * Reset form
 */
function resetForm() {
  $("#lexicalSearchForm")[0].reset();
  hideResults();
  showLoading(false);
}

/**
 * Show alert message
 */
function showAlert(message, type = "info") {
  const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

  // Remove existing alerts
  $(".alert").remove();

  // Add new alert
  $(".container-fluid").prepend(alertHtml);

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    $(".alert").fadeOut();
  }, 5000);
}
