document.addEventListener('DOMContentLoaded', function () {
  const queryList = document.getElementById('query-list');
  const formAddQuery = document.getElementById('form-add-query');
  const queryText = document.getElementById('query-text');
  const relevantVerseSection = document.getElementById('relevant-verse-section');
  const relevantVerseList = document.getElementById('relevant-verse-list');
  const evaluasiBtn = document.getElementById('evaluasi-btn');
  const evaluasiResult = document.getElementById('evaluasi-result');
  const logBtn = document.getElementById('log-btn');
  const logModal = new bootstrap.Modal(document.getElementById('logModal'));
  const logContent = document.getElementById('log-content');
  const ayatDetailModal = new bootstrap.Modal(document.getElementById('ayatDetailModal'));
  const ayatDetailContent = document.getElementById('ayat-detail-content');

  let selectedQueryId = null;

  function showSpinner(el, msg = 'Memuat...') {
    el.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>${msg}</div></div>`;
  }

  function loadQueries() {
    showSpinner(queryList, 'Memuat query...');
    fetch('/api/query')
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          renderQueryList(data.data);
        }
      });
  }

  function renderQueryList(queries) {
    document.getElementById('query-count').textContent = queries.length;
    let html = '<ul class="list-group">';
    queries.forEach((q) => {
      html += `<li class="list-group-item d-flex justify-content-between align-items-center ${selectedQueryId === q.id ? 'active fw-bold' : ''}" style="cursor:pointer" data-id="${q.id}">
        <span>${q.text}</span>
        <div>
          <button class="btn btn-sm btn-info btn-detail-query me-2" data-id="${q.id}"><i class="fas fa-list"></i> Detail</button>
          <button class="btn btn-sm btn-danger btn-delete-query" data-id="${q.id}"><i class="fas fa-trash"></i></button>
        </div>
      </li>`;
    });
    html += '</ul>';
    queryList.innerHTML = html;
    // Event pilih query
    document.querySelectorAll('#query-list .list-group-item').forEach((el) => {
      el.addEventListener('click', function (e) {
        if (e.target.classList.contains('btn-delete-query') || e.target.classList.contains('btn-detail-query')) return;
        selectedQueryId = parseInt(this.getAttribute('data-id'));
        loadRelevantVerses(selectedQueryId);
        renderQueryList(queries);
        evaluasiBtn.classList.remove('d-none');
        logBtn.classList.remove('d-none');
        evaluasiResult.innerHTML = '';
        loadEvaluationResults(selectedQueryId);
      });
    });
    // Event hapus query
    document.querySelectorAll('.btn-delete-query').forEach((btn) => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const id = this.getAttribute('data-id');
        if (confirm('Hapus query ini beserta ayat relevannya?')) {
          fetch(`/api/query/${id}`, { method: 'DELETE' })
            .then((res) => res.json())
            .then(() => {
              if (selectedQueryId == id) {
                selectedQueryId = null;
                relevantVerseList.innerHTML = '';
                evaluasiBtn.classList.add('d-none');
                logBtn.classList.add('d-none');
                evaluasiResult.innerHTML = '';
                document.getElementById('ayat-count').textContent = 0;
              }
              loadQueries();
            });
        }
      });
    });
    // Event detail query
    document.querySelectorAll('.btn-detail-query').forEach((btn) => {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        const id = this.getAttribute('data-id');
        showAllAyatDetailModal(id);
      });
    });
  }

  async function showAllAyatDetailModal(queryId) {
    showSpinner(ayatDetailContent, 'Memuat detail ayat...');
    // Ambil semua ayat relevan
    const res = await fetch(`/api/query/${queryId}/relevant_verses`);
    const data = await res.json();
    if (!data.success) {
      ayatDetailContent.innerHTML = '<div class="text-danger">Gagal memuat ayat relevan.</div>';
      ayatDetailModal.show();
      return;
    }
    if (!data.data.length) {
      ayatDetailContent.innerHTML = '<div class="text-muted">Tidak ada ayat relevan.</div>';
      ayatDetailModal.show();
      return;
    }
    // Fetch detail semua ayat
    let html = '<ul class="list-group mb-3">';
    for (const v of data.data) {
      const [surah, ayat] = v.verse_ref.split(':');
      try {
        showSpinner(ayatDetailContent, 'Memuat detail ayat...');
        const detailRes = await fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`);
        const detailData = await detailRes.json();
        if (detailData.success && detailData.ayat) {
          const a = detailData.ayat;
          html += `<li class='list-group-item d-flex justify-content-between align-items-center'>
            <div>
              <div><strong>${a.surah_name} (${a.surah}) : ${a.ayat}</strong></div>
              <div class='text-arab' style='font-size:1.2em'>${a.text}</div>
              <div><em>${a.translation || ''}</em></div>
            </div>
            <button class='btn btn-sm btn-danger btn-delete-verse-modal' data-id='${v.id}'><i class='fas fa-trash'></i></button>
          </li>`;
        } else {
          html += `<li class='list-group-item text-danger'>Detail ayat tidak ditemukan untuk ${v.verse_ref}.</li>`;
        }
      } catch {
        html += `<li class='list-group-item text-danger'>Gagal memuat detail ayat untuk ${v.verse_ref}.</li>`;
      }
    }
    html += '</ul>';
    ayatDetailContent.innerHTML = html;
    ayatDetailModal.show();
    // Event hapus ayat di modal
    document.querySelectorAll('.btn-delete-verse-modal').forEach((btn) => {
      btn.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        showSpinner(ayatDetailContent, 'Menghapus ayat...');
        fetch(`/api/query/relevant_verse/${id}`, { method: 'DELETE' })
          .then((res) => res.json())
          .then(() => showAllAyatDetailModal(queryId));
      });
    });
  }

  formAddQuery.addEventListener('submit', function (e) {
    e.preventDefault();
    const text = queryText.value.trim();
    if (!text) return;
    fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
      .then((res) => res.json())
      .then(() => {
        queryText.value = '';
        loadQueries();
      });
  });

  function loadRelevantVerses(queryId) {
    fetch(`/api/query/${queryId}/relevant_verses`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          renderRelevantVerses(data.data);
          document.getElementById('ayat-count').textContent = data.data.length;
        }
      });
  }

  function renderRelevantVerses(verses) {
    // Tampilkan setiap ayat sebagai badge
    let html = '';
    verses.forEach((v) => {
      html += `<span class="badge bg-primary me-1 mb-1">${v.verse_ref}</span>`;
    });
    relevantVerseList.innerHTML = html;
  }

  // Form tambah ayat di modal
  document.getElementById('form-add-verse-modal').addEventListener('submit', function (e) {
    e.preventDefault();
    const verse = document.getElementById('verse-ref-modal').value.trim();
    if (!verse || !selectedQueryId) return;
    showSpinner(ayatDetailContent, 'Menambah ayat...');
    fetch(`/api/query/${selectedQueryId}/relevant_verses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ verse_ref: verse }),
    })
      .then((res) => res.json())
      .then(() => {
        document.getElementById('verse-ref-modal').value = '';
        showAllAyatDetailModal(selectedQueryId);
        loadRelevantVerses(selectedQueryId);
      });
  });

  // Tampilkan form tambah ayat hanya jika query dipilih
  queryList.addEventListener('click', function () {
    if (selectedQueryId) {
      evaluasiBtn.classList.remove('d-none');
      logBtn.classList.remove('d-none');
    }
  });

  evaluasiBtn.addEventListener('click', function () {
    if (!selectedQueryId) return;
    evaluasiBtn.disabled = true;
    evaluasiBtn.textContent = 'Evaluasi...';
    evaluasiResult.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-warning" role="status"></div><div>Memproses evaluasi...</div></div>';
    fetch(`/api/query/${selectedQueryId}/evaluate`, { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        evaluasiBtn.disabled = false;
        evaluasiBtn.textContent = 'Evaluasi';
        if (data.success) {
          let html = '<h5>Hasil Evaluasi</h5>';
          html += '<table class="table table-bordered"><thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>Waktu (s)</th></tr></thead><tbody>';
          data.results.forEach(r => {
            html += `<tr><td>${r.model}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td><td>${r.exec_time}</td></tr>`;
          });
          html += '</tbody></table>';
          evaluasiResult.innerHTML = html;
        } else {
          evaluasiResult.innerHTML = `<div class='alert alert-danger'>${data.message}</div>`;
        }
      })
      .catch(() => {
        evaluasiBtn.disabled = false;
        evaluasiBtn.textContent = 'Evaluasi';
        evaluasiResult.innerHTML = `<div class='alert alert-danger'>Terjadi kesalahan saat evaluasi.</div>`;
      });
  });

  function loadEvaluationResults(queryId) {
    showSpinner(evaluasiResult, 'Memuat hasil evaluasi...');
    fetch(`/api/query/${queryId}/evaluation_results`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.results.length > 0) {
          let html = '<h5>Hasil Evaluasi Terakhir</h5>';
          html += '<table class="table table-bordered"><thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>Waktu (s)</th></tr></thead><tbody>';
          data.results.forEach(r => {
            html += `<tr><td>${r.model}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td><td>${r.exec_time}</td></tr>`;
          });
          html += '</tbody></table>';
          evaluasiResult.innerHTML = html;
        } else {
          evaluasiResult.innerHTML = '';
        }
      });
  }

  logBtn.addEventListener('click', function () {
    if (!selectedQueryId) return;
    showSpinner(logContent, 'Memuat log...');
    fetch(`/api/query/${selectedQueryId}/evaluation_logs`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.logs.length > 0) {
          let html = '<table class="table table-sm table-bordered"><thead><tr><th>Waktu</th><th>Model</th><th>Skor Lama</th><th>Skor Baru</th></tr></thead><tbody>';
          data.logs.forEach(l => {
            html += `<tr><td>${l.changed_at}</td><td>${l.model}</td><td>${l.old_score}</td><td>${l.new_score}</td></tr>`;
          });
          html += '</tbody></table>';
          logContent.innerHTML = html;
        } else {
          logContent.innerHTML = '<div class="text-muted">Belum ada log perubahan.</div>';
        }
      });
    logModal.show();
  });

  loadQueries();
}); 