$(document).ready(function () {
  // Ambil pengaturan user dan set limit & threshold
  fetch('/api/models/user_settings')
    .then(res => res.json())
    .then(data => {
      if (data.success && data.data) {
        const limit = data.data.result_limit;
        const threshold = data.data.threshold;
        if (limit !== undefined && limit !== null) {
          $('#limit').val(limit);
        }
        if (threshold !== undefined && threshold !== null) {
          $('#threshold').val(threshold);
          $('#thresholdValue').text(threshold);
        }
      }
    });
  // Handle form submission
  $("#semanticSearchForm").submit(function (e) {
    e.preventDefault();
    performSemanticSearch();
  });

  // Handle reset button
  $("#resetBtn").click(function () {
    resetForm();
  });

  // Handle threshold slider
  $("#threshold").on("input", function () {
    $("#thresholdValue").text($(this).val());
  });

  // Check URL parameters for auto-search
  const urlParams = new URLSearchParams(window.location.search);
  const queryParam = urlParams.get("query");
  if (queryParam) {
    $("#query").val(queryParam);
    setTimeout(() => {
      performSemanticSearch();
    }, 500);
  }
});

function performSemanticSearch() {
  const query = $("#query").val().trim();
  const model = $("#model").val();
  const limit = $("#limit").val();
  const threshold = $("#threshold").val();
  const showDetails = $("#showDetails").is(":checked");

  if (!query) {
    showAlert("Masukkan kata kunci pencarian.", "warning");
    return;
  }

  showLoading(true);
  hideResults();

  const requestData = {
    query: query,
    model: model,
    limit: parseInt(limit) || null, // Jika 0, kirim null untuk tak terbatas
    threshold: parseFloat(threshold),
  };

  $.ajax({
    type: "POST",
    url: "/api/search/search",
    contentType: "application/json",
    data: JSON.stringify(requestData),
    success: function (response) {
      showLoading(false);

      if (response.success) {
        displayResults(response.data, showDetails);
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

function displayResults(data, showDetails) {
  const resultsContainer = $("#searchResults");
  const resultsCard = $("#resultsCard");
  const noResultsCard = $("#noResultsCard");

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
                    Model: ${getModelLabel(data.model)} | Threshold: ${
    data.threshold
  } | Waktu: ${data.execution_time}s
                </div>
            </div>
        </div>
    `;

  // Display each result
  data.results.forEach((result, index) => {
    const resultClass = index % 2 === 0 ? "bg-light" : "";
    const similarityBadge = getSimilarityBadge(
      result.similarity,
      result.individual_scores,
      showDetails
    );

    resultsHtml += `
            <div class="list-group-item ${resultClass}">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">Surah ${result.surah_number} (${
      result.surah_name
    }), Ayat ${result.ayat_number}</h5>
                </div>
                <p class="mb-1 arabic-text text-end">${result.arabic}</p>
                <p class="mb-1">${result.translation}</p>
                ${
                  result.classification
                    ? `<div class="small text-muted mt-1">Klasifikasi: ${result.classification.title}</div>`
                    : ""
                }
                <div class="small text-muted mt-2">
                    <strong>Skor kesamaan:</strong> ${parseFloat(
                      result.similarity
                    ).toFixed(4)}
                    ${
                      result.individual_scores && showDetails
                        ? `
                        <br><strong>Detail model:</strong> 
                        Word2Vec: ${(
                          result.individual_scores.word2vec * 100
                        ).toFixed(
                          2
                        )}% (${result.individual_scores.word2vec.toFixed(4)}), 
                        FastText: ${(
                          result.individual_scores.fasttext * 100
                        ).toFixed(
                          2
                        )}% (${result.individual_scores.fasttext.toFixed(4)}), 
                        GloVe: ${(result.individual_scores.glove * 100).toFixed(
                          2
                        )}% (${result.individual_scores.glove.toFixed(4)})
                    `
                        : ""
                    }
                </div>
            </div>
        `;
  });

  resultsContainer.html(resultsHtml);
  resultsCard.removeClass("d-none");

  $("html, body").animate(
    {
      scrollTop: resultsCard.offset().top - 20,
    },
    500
  );
}

function getModelLabel(model) {
  const labels = {
    word2vec: "Word2Vec",
    fasttext: "FastText",
    glove: "GloVe",
    ensemble: "Ensemble (Averaging)",
  };
  return labels[model] || model;
}

function getSimilarityBadge(similarity, individualScores, showDetails) {
  const similarityValue = parseFloat(similarity);
  const similarityPercentage = Math.round(similarityValue * 100);

  let badgeClass = "bg-secondary";
  if (similarityPercentage >= 80) {
    badgeClass = "bg-success";
  } else if (similarityPercentage >= 60) {
    badgeClass = "bg-primary";
  } else if (similarityPercentage >= 40) {
    badgeClass = "bg-info";
  }

  let tooltipText = `Skor kesamaan: ${similarityValue.toFixed(4)}`;

  if (individualScores && showDetails) {
    tooltipText += `\nWord2Vec: ${(individualScores.word2vec * 100).toFixed(
      2
    )}% (${individualScores.word2vec.toFixed(4)})`;
    tooltipText += `\nFastText: ${(individualScores.fasttext * 100).toFixed(
      2
    )}% (${individualScores.fasttext.toFixed(4)})`;
    tooltipText += `\nGloVe: ${(individualScores.glove * 100).toFixed(
      2
    )}% (${individualScores.glove.toFixed(4)})`;
  }

  let badge = `<span class="badge ${badgeClass} float-end" title="${tooltipText}">${similarityPercentage}% relevan</span>`;

  if (individualScores && showDetails) {
    const scoresText = `Word2Vec: ${(individualScores.word2vec * 100).toFixed(
      2
    )}% (${individualScores.word2vec.toFixed(4)}), FastText: ${(
      individualScores.fasttext * 100
    ).toFixed(2)}% (${individualScores.fasttext.toFixed(4)}), GloVe: ${(
      individualScores.glove * 100
    ).toFixed(2)}% (${individualScores.glove.toFixed(4)})`;
    badge += `<br><small class="text-muted">${scoresText}</small>`;
  }

  return badge;
}

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

function hideResults() {
  $("#resultsCard").addClass("d-none");
  $("#noResultsCard").addClass("d-none");
}

function resetForm() {
  $("#semanticSearchForm")[0].reset();
  $("#thresholdValue").text("0.5");
  hideResults();
  showLoading(false);
}

function showAlert(message, type = "info") {
  const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

  $(".alert").remove();
  $(".container-fluid").prepend(alertHtml);

  setTimeout(() => {
    $(".alert").fadeOut();
  }, 5000);
}
