function renderTraceFinalResults(finalResults, container) {
  if (!Array.isArray(finalResults) || finalResults.length === 0) {
    container.innerHTML = '<div class="alert alert-warning">Tidak ada hasil akhir.</div>';
    return;
  }
  let html = `<div class='table-responsive'><table class='table table-bordered table-sm align-middle'>`;
  html += `<thead><tr><th>No</th><th>Verse ID</th><th>Similarity</th><th>Boosted</th><th>Source Query</th></tr></thead><tbody>`;
  finalResults.forEach((r, i) => {
    const verseId = r.verse_id || (r.surah_number && r.ayat_number ? `${r.surah_number}:${r.ayat_number}` : '-');
    html += `<tr>`;
    html += `<td>${i + 1}</td>`;
    html += `<td><span class='badge bg-primary'>${verseId}</span></td>`;
    html += `<td>${formatSimilarity(r.similarity)}</td>`;
    html += `<td>${r.boosted ? '<span class="badge bg-success">Ya</span>' : '<span class="badge bg-secondary">Tidak</span>'}</td>`;
    html += `<td><span class='badge bg-info text-dark'>${r.source_query || '-'}</span></td>`;
    html += `</tr>`;
  });
  html += `</tbody></table></div>`;
  container.innerHTML = html;
}

function formatSimilarity(sim) {
  if (typeof sim !== 'number') return '-';
  return (sim * 100).toFixed(1) + '%';
}

function renderStepTabs(data, idx, stepType) {
  // Tab nav
  let html = `<ul class="nav nav-tabs mb-2" id="stepTab${idx}" role="tablist">`;
  html += `<li class="nav-item" role="presentation">
    <button class="nav-link active" id="tab-summary-${idx}" data-bs-toggle="tab" data-bs-target="#tab-summary-pane-${idx}" type="button" role="tab" aria-controls="tab-summary-pane-${idx}" aria-selected="true">Ringkasan</button>
  </li>`;
  html += `<li class="nav-item" role="presentation">
    <button class="nav-link" id="tab-raw-${idx}" data-bs-toggle="tab" data-bs-target="#tab-raw-pane-${idx}" type="button" role="tab" aria-controls="tab-raw-pane-${idx}" aria-selected="false">Data Asli</button>
  </li>`;
  html += `</ul>`;
  // Tab content
  html += `<div class="tab-content" id="stepTabContent${idx}">`;
  html += `<div class="tab-pane fade show active" id="tab-summary-pane-${idx}" role="tabpanel" aria-labelledby="tab-summary-${idx}">`;
  html += renderStepSummary(data, stepType);
  html += `</div>`;
  html += `<div class="tab-pane fade" id="tab-raw-pane-${idx}" role="tabpanel" aria-labelledby="tab-raw-${idx}">`;
  html += `<pre style='white-space:pre-wrap; word-break:break-all;'>${JSON.stringify(data, null, 2)}</pre>`;
  html += `</div>`;
  html += `</div>`;
  return html;
}

function renderStepSummary(data, stepType) {
  if (stepType === 'ontology_expansion') {
    let html = '';
    if (data.main_concept) {
      html += `<div><b>Main Concept:</b> <span class='badge bg-primary'>${data.main_concept.label || data.main_concept.id}</span></div>`;
    }
    if (data.expanded_queries) {
      html += `<div class='mt-2'><b>Expanded Queries:</b> `;
      data.expanded_queries.forEach(q => {
        html += `<span class='badge bg-info text-dark me-1'>${q}</span>`;
      });
      html += `</div>`;
    }
    if (data.ontology_data && Array.isArray(data.ontology_data)) {
      html += `<div class='mt-2'><b>Jumlah Konsep Terkait:</b> ${data.ontology_data.length}</div>`;
    }
    return html || '<em>Tidak ada ringkasan.</em>';
  }
  if (stepType === 'semantic_search') {
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      // Tabel ringkasan subtrace
      let html = `<div class='table-responsive'><table class='table table-sm table-bordered'><thead><tr><th>No</th><th>Query</th><th>Jumlah Langkah</th><th>Jumlah Log</th><th>Jumlah Hasil</th></tr></thead><tbody>`;
      data.forEach((sub, i) => {
        html += `<tr>`;
        html += `<td>${i + 1}</td>`;
        html += `<td><span class='badge bg-primary'>${sub.query || '-'}</span></td>`;
        html += `<td>${sub.steps ? sub.steps.length : 0}</td>`;
        html += `<td>${sub.logs ? sub.logs.length : 0}</td>`;
        // Coba ambil jumlah hasil dari steps terakhir jika ada
        let hasil = '-';
        if (sub.steps && sub.steps.length > 0) {
          const lastStep = sub.steps[sub.steps.length - 1];
          if (lastStep.data && Array.isArray(lastStep.data)) {
            hasil = lastStep.data.length;
          }
        }
        html += `<td>${hasil}</td>`;
        html += `</tr>`;
      });
      html += `</tbody></table></div>`;
      return html;
    }
    return `<em>Data tidak tersedia.</em>`;
  }
  if (stepType === 'boosting_ranking') {
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      let html = `<div class='table-responsive'><table class='table table-sm table-bordered'><thead><tr><th>No</th><th>Verse ID</th><th>Before</th><th>After</th><th>Source Query</th></tr></thead><tbody>`;
      data.forEach((b, i) => {
        html += `<tr>`;
        html += `<td>${i + 1}</td>`;
        html += `<td><span class='badge bg-primary'>${b.verse_id || '-'}</span></td>`;
        html += `<td>${formatSimilarity(b.before)}</td>`;
        html += `<td>${formatSimilarity(b.after)}</td>`;
        html += `<td><span class='badge bg-info text-dark'>${b.source_query || '-'}</span></td>`;
        html += `</tr>`;
      });
      html += `</tbody></table></div>`;
      return html;
    }
    return `<em>Tidak ada boosting.</em>`;
  }
  if (typeof data === 'object' && data !== null) {
    let keys = Object.keys(data);
    if (keys.length > 0) {
      let html = '<ul>';
      keys.forEach(k => {
        if (typeof data[k] !== 'object') {
          html += `<li><b>${k}:</b> ${data[k]}</li>`;
        }
      });
      html += '</ul>';
      return html;
    }
  }
  return '<em>Tidak ada ringkasan.</em>';
}

function renderStepCard(step, idx) {
  // Ikon per step
  const stepIcons = {
    'ontology_expansion': 'fa-sitemap',
    'semantic_search': 'fa-search',
    'boosting_ranking': 'fa-bolt',
    'default': 'fa-cube'
  };
  const icon = stepIcons[step.step] || stepIcons['default'];
  // Jumlah hasil (jika ada)
  let badge = '';
  if (step.step === 'ontology_expansion' && step.data && step.data.expanded_queries) {
    badge = `<span class='badge bg-info ms-2'>${step.data.expanded_queries.length} ekspansi</span>`;
  }
  if (step.step === 'semantic_search' && Array.isArray(step.data)) {
    badge = `<span class='badge bg-info ms-2'>${step.data.length} query</span>`;
  }
  if (step.step === 'boosting_ranking' && Array.isArray(step.data)) {
    badge = `<span class='badge bg-info ms-2'>${step.data.length} boosting</span>`;
  }
  // Waktu proses (jika ada)
  let timeInfo = '';
  if (step.data && step.data.duration_ms) {
    timeInfo = `<span class='badge bg-secondary ms-2'><i class='fa fa-clock me-1'></i>${step.data.duration_ms} ms</span>`;
  }
  // Log per step
  let logHtml = '';
  if (step.logs && step.logs.length > 0) {
    logHtml = `<div class='mt-2'><b>Log Step:</b><ul class='small'>`;
    step.logs.forEach(l => {
      logHtml += `<li>${l}</li>`;
    });
    logHtml += `</ul></div>`;
  }
  // Tab data
  let tabHtml = '';
  if (Array.isArray(step.data)) {
    tabHtml = `<div class='accordion' id='subAccordion${idx}'>`;
    step.data.forEach((sub, subIdx) => {
      tabHtml += `<div class='accordion-item'>
        <h2 class='accordion-header' id='subHeading${idx}_${subIdx}'>
          <button class='accordion-button collapsed' type='button' data-bs-toggle='collapse' data-bs-target='#subCollapse${idx}_${subIdx}' aria-expanded='false' aria-controls='subCollapse${idx}_${subIdx}'>
            Sub-step: ${sub.query || subIdx + 1}
          </button>
        </h2>
        <div id='subCollapse${idx}_${subIdx}' class='accordion-collapse collapse' aria-labelledby='subHeading${idx}_${subIdx}' data-bs-parent='#subAccordion${idx}'>
          <div class='accordion-body'>
            ${renderStepTabs(sub, `${idx}_${subIdx}`, step.step)}
          </div>
        </div>
      </div>`;
    });
    tabHtml += `</div>`;
  } else {
    tabHtml = renderStepTabs(step.data, idx, step.step);
  }
  return `
    <div class='card mb-3 shadow-sm'>
      <div class='card-header bg-light d-flex align-items-center'>
        <i class='fa ${icon} me-2'></i>
        <b>Step ${idx + 1}: ${step.step.replace('_', ' ').toUpperCase()}</b>
        ${badge}
        ${timeInfo}
      </div>
      <div class='card-body'>
        ${tabHtml}
        ${logHtml}
      </div>
    </div>
  `;
}

window.renderTraceFinalResults = renderTraceFinalResults;
window.renderStepTabs = renderStepTabs;
window.renderStepCard = renderStepCard; 