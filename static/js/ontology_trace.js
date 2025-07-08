function renderTraceFinalResults(finalResults, container) {
  if (!Array.isArray(finalResults) || finalResults.length === 0) {
    container.innerHTML = '<div class="alert alert-warning">Tidak ada hasil akhir.</div>';
    return;
  }
  let html = `<div class='table-responsive'><table class='table table-bordered table-sm align-middle'>`;
  html += `<thead><tr><th>No</th><th>Verse ID</th><th>Similarity</th><th>Boosted</th><th>Source Query</th><th>Aksi</th></tr></thead><tbody>`;
  finalResults.forEach((r, i) => {
    const verseId = r.verse_id || (r.surah_number && r.ayat_number ? `${r.surah_number}:${r.ayat_number}` : '-');
    html += `<tr>`;
    html += `<td>${i + 1}</td>`;
    html += `<td><span class='badge bg-primary'>${verseId}</span></td>`;
    html += `<td>${formatSimilarity(r.similarity)}</td>`;
    html += `<td>${r.boosted ? '<span class="badge bg-success">Ya</span>' : '<span class="badge bg-secondary">Tidak</span>'}</td>`;
    html += `<td><span class='badge bg-info text-dark'>${r.source_query || '-'}</span></td>`;
    html += `<td><button class='btn btn-sm btn-outline-info' onclick='showVerseDetail(${JSON.stringify(r).replace(/"/g, "&quot;")})'><i class='fas fa-eye'></i> Detail</button></td>`;
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
      html += `<div class='mb-2'><b>Main Concept:</b> <span class='badge bg-primary'>${data.main_concept.label || data.main_concept.id}</span>`;
      html += `<button class='btn btn-sm btn-outline-primary ms-2' onclick='showOntologyDetail(${JSON.stringify(data.main_concept).replace(/"/g, "&quot;")})'><i class='fas fa-eye'></i> Detail</button></div>`;
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
      if (data.ontology_data.length > 0) {
        html += `<div class='mt-2'><b>Konsep Terkait:</b><br>`;
        data.ontology_data.forEach((concept, i) => {
          html += `<span class='badge bg-secondary me-1 mb-1'>${concept.label || concept.id}</span>`;
          if (i < 3) { // Tampilkan maksimal 3 konsep dengan tombol detail
            html += `<button class='btn btn-sm btn-outline-secondary ms-1 mb-1' onclick='showOntologyDetail(${JSON.stringify(concept).replace(/"/g, "&quot;")})'><i class='fas fa-eye'></i></button>`;
          }
        });
        if (data.ontology_data.length > 3) {
          html += `<span class='badge bg-light text-dark'>+${data.ontology_data.length - 3} lagi</span>`;
        }
        html += `</div>`;
      }
    }
    return html || '<em>Tidak ada ringkasan.</em>';
  }
  if (stepType === 'semantic_search') {
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      // Tabel ringkasan subtrace
      let html = `<div class='table-responsive'><table class='table table-sm table-bordered'><thead><tr><th>No</th><th>Query</th><th>Jumlah Langkah</th><th>Jumlah Log</th><th>Jumlah Hasil</th><th>Aksi</th></tr></thead><tbody>`;
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
        html += `<td><button class='btn btn-sm btn-outline-info' onclick='showSubTraceDetail(${JSON.stringify(sub).replace(/"/g, "&quot;")}, ${i})'><i class='fas fa-eye'></i> Detail</button></td>`;
        html += `</tr>`;
      });
      html += `</tbody></table></div>`;
      return html;
    }
    return `<em>Data tidak tersedia.</em>`;
  }
  if (stepType === 'boosting_ranking') {
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      let html = `<div class='table-responsive'><table class='table table-sm table-bordered'><thead><tr><th>No</th><th>Verse ID</th><th>Before</th><th>After</th><th>Source Query</th><th>Peningkatan</th></tr></thead><tbody>`;
      data.forEach((b, i) => {
        const increase = ((b.after - b.before) * 100).toFixed(1);
        const increaseClass = increase > 0 ? 'text-success' : 'text-secondary';
        html += `<tr>`;
        html += `<td>${i + 1}</td>`;
        html += `<td><span class='badge bg-primary'>${b.verse_id || '-'}</span></td>`;
        html += `<td>${formatSimilarity(b.before)}</td>`;
        html += `<td>${formatSimilarity(b.after)}</td>`;
        html += `<td><span class='badge bg-info text-dark'>${b.source_query || '-'}</span></td>`;
        html += `<td class='${increaseClass}'><i class='fas fa-arrow-up'></i> ${increase}%</td>`;
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
  
  // Penjelasan teori per step
  const stepExplanations = {
    'ontology_expansion': {
      title: 'Ekspansi Ontologi',
      theory: 'Sistem mencari konsep-konsep terkait dengan kata kunci Anda dalam struktur pengetahuan (ontologi). Ini seperti ketika Anda mencari "makanan", sistem juga akan mencari "nasi", "roti", "buah" yang terkait dengan konsep makanan.',
      process: 'Sistem menganalisis kata kunci dan menemukan sinonim, konsep terkait, dan relasi hierarkis untuk memperluas pencarian.',
      benefit: 'Memastikan tidak ada ayat relevan yang terlewat karena perbedaan istilah atau sinonim.'
    },
    'semantic_search': {
      title: 'Pencarian Semantik',
      theory: 'Sistem menggunakan model AI (Word2Vec, FastText, atau GloVe) untuk memahami makna kata-kata. Model ini telah belajar dari jutaan teks dan dapat menghitung seberapa mirip makna antara kata kunci dan ayat-ayat Al-Qur\'an.',
      process: 'Setiap kata kunci (termasuk hasil ekspansi) diubah menjadi vektor angka, kemudian dibandingkan dengan vektor ayat-ayat untuk mencari yang paling mirip.',
      benefit: 'Menemukan ayat yang bermakna serupa meskipun menggunakan kata yang berbeda.'
    },
    'boosting_ranking': {
      title: 'Boosting & Ranking',
      theory: 'Sistem memberikan "bonus skor" pada ayat yang ditemukan melalui ekspansi ontologi, karena ini menunjukkan relevansi yang lebih tinggi. Kemudian semua hasil diurutkan berdasarkan skor akhir.',
      process: 'Ayat yang ditemukan dari query ekspansi mendapat tambahan skor 0.1, kemudian semua hasil diurutkan dari skor tertinggi ke terendah.',
      benefit: 'Hasil yang lebih relevan akan muncul di urutan teratas, memudahkan pengguna menemukan informasi yang dicari.'
    }
  };
  
  const stepExplanation = stepExplanations[step.step] || {
    title: step.step.replace('_', ' ').toUpperCase(),
    theory: 'Proses ini melibatkan analisis data dan pengolahan informasi untuk menghasilkan hasil yang relevan.',
    process: 'Sistem memproses data sesuai dengan algoritma yang telah ditentukan.',
    benefit: 'Menghasilkan output yang terstruktur dan dapat dianalisis.'
  };
  
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
  
  // Tombol detail step
  const detailButton = `<button class='btn btn-sm btn-outline-primary ms-2' onclick='showStepDetail(${JSON.stringify(step).replace(/"/g, "&quot;")}, ${idx})'><i class='fas fa-info-circle'></i> Detail Lengkap</button>`;
  
  // Penjelasan teori untuk step ini
  const theoryHtml = `
    <div class='alert alert-light border-start border-primary border-4 mb-3'>
      <div class='row'>
        <div class='col-md-4'>
          <h6 class='text-primary'><i class='fas fa-lightbulb me-2'></i>Teori</h6>
          <p class='small text-muted'>${stepExplanation.theory}</p>
        </div>
        <div class='col-md-4'>
          <h6 class='text-success'><i class='fas fa-cogs me-2'></i>Proses</h6>
          <p class='small text-muted'>${stepExplanation.process}</p>
        </div>
        <div class='col-md-4'>
          <h6 class='text-info'><i class='fas fa-chart-line me-2'></i>Manfaat</h6>
          <p class='small text-muted'>${stepExplanation.benefit}</p>
        </div>
      </div>
    </div>
  `;
  
  return `
    <div class='card mb-3 shadow-sm'>
      <div class='card-header bg-light d-flex align-items-center justify-content-between'>
        <div class='d-flex align-items-center'>
          <i class='fa ${icon} me-2'></i>
          <b>Step ${idx + 1}: ${stepExplanation.title}</b>
          ${badge}
          ${timeInfo}
        </div>
        ${detailButton}
      </div>
      <div class='card-body'>
        ${theoryHtml}
        ${tabHtml}
        ${logHtml}
      </div>
    </div>
  `;
}

// Fungsi untuk menampilkan detail sub-trace
window.showSubTraceDetail = function(subTraceData, subIndex) {
  const modal = new bootstrap.Modal(document.getElementById('stepDetailModal'));
  const content = document.getElementById('stepDetailContent');
  const title = document.getElementById('stepDetailModalLabel');
  
  title.innerHTML = `<i class="fas fa-search me-2"></i>Detail Sub-Trace: ${subTraceData.query || `Sub-${subIndex + 1}`}`;
  
  let html = '';
  html += `<div class="row">`;
  html += `<div class="col-md-6">`;
  html += `<h6><i class="fas fa-list me-2"></i>Ringkasan Sub-Trace</h6>`;
  html += `<table class="table table-sm">`;
  html += `<tr><td><strong>Query:</strong></td><td><span class="badge bg-primary">${subTraceData.query || '-'}</span></td></tr>`;
  html += `<tr><td><strong>Jumlah Steps:</strong></td><td>${subTraceData.steps ? subTraceData.steps.length : 0}</td></tr>`;
  html += `<tr><td><strong>Jumlah Logs:</strong></td><td>${subTraceData.logs ? subTraceData.logs.length : 0}</td></tr>`;
  html += `</table>`;
  html += `</div>`;
  html += `<div class="col-md-6">`;
  html += `<h6><i class="fas fa-steps me-2"></i>Steps Detail</h6>`;
  if (subTraceData.steps && subTraceData.steps.length > 0) {
    html += `<div class="list-group">`;
    subTraceData.steps.forEach((step, i) => {
      html += `<div class="list-group-item list-group-item-action">`;
      html += `<div class="d-flex w-100 justify-content-between">`;
      html += `<h6 class="mb-1">Step ${i + 1}: ${step.step}</h6>`;
      html += `<small>${step.data ? Object.keys(step.data).length : 0} data</small>`;
      html += `</div>`;
      if (step.data) {
        html += `<p class="mb-1"><small>Data: ${JSON.stringify(step.data).substring(0, 100)}...</small></p>`;
      }
      html += `</div>`;
    });
    html += `</div>`;
  } else {
    html += `<p><em>Tidak ada steps</em></p>`;
  }
  html += `</div>`;
  html += `</div>`;
  
  html += `<div class="mt-3">`;
  html += `<h6><i class="fas fa-code me-2"></i>Data Lengkap Sub-Trace</h6>`;
  html += `<div class="bg-light p-3 rounded">`;
  html += `<pre style="max-height: 400px; overflow: auto;">${JSON.stringify(subTraceData, null, 2)}</pre>`;
  html += `</div>`;
  html += `</div>`;
  
  if (subTraceData.logs && subTraceData.logs.length > 0) {
    html += `<div class="mt-3">`;
    html += `<h6><i class="fas fa-terminal me-2"></i>Log Sub-Trace</h6>`;
    html += `<div class="bg-dark text-light p-3 rounded">`;
    html += `<pre style="max-height: 200px; overflow: auto;">${subTraceData.logs.join('\n')}</pre>`;
    html += `</div>`;
    html += `</div>`;
  }
  
  content.innerHTML = html;
  modal.show();
};

window.renderTraceFinalResults = renderTraceFinalResults;
window.renderStepTabs = renderStepTabs;
window.renderStepCard = renderStepCard; 