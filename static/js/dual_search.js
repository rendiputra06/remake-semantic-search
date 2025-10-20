// Dual Search page JS
(function(){
  // Toggle advanced panel
  const toggleBtn = document.getElementById('toggle-advanced');
  const adv = document.getElementById('ds-advanced');
  if (toggleBtn && adv) {
    toggleBtn.addEventListener('click', function(){
      adv.style.display = (adv.style.display === 'none' ? 'block' : 'none');
    });
  }

  // Slider labels
  ['a_weight','b_weight','w2v_weight','ft_weight','glove_weight'].forEach(function(id){
    const el = document.getElementById(id);
    const valEl = document.getElementById(id + '_val');
    if (el && valEl) {
      el.addEventListener('input', function(){ valEl.textContent = this.value; });
    }
  });

  // Update labels & toggle ensemble-only fields
  function updateABLabels() {
    const comboEl = document.getElementById('combo');
    if (!comboEl) return;
    const combo = comboEl.value;
    const aLbl = document.getElementById('a_weight_label');
    const bLbl = document.getElementById('b_weight_label');
    const map = {
      'w2v_ft': ['Word2Vec (A)','FastText (B)'],
      'w2v_glove': ['Word2Vec (A)','GloVe (B)'],
      'ft_glove': ['FastText (A)','GloVe (B)'],
      'ensemble3': ['-','-']
    };
    const labels = map[combo] || ['A','B'];
    if (aLbl) aLbl.textContent = labels[0];
    if (bLbl) bLbl.textContent = labels[1];
    const showEnsemble = (combo === 'ensemble3');
    ['method','use_voting_filter','w2v_weight','ft_weight','glove_weight'].forEach(function(id){
      const el = document.getElementById(id);
      const parent = el ? el.closest('.col-md-3, .col-md-2') : null;
      if (el && parent) parent.style.display = showEnsemble ? '' : 'none';
    });
  }
  const comboEl = document.getElementById('combo');
  if (comboEl) {
    comboEl.addEventListener('change', updateABLabels);
    updateABLabels();
  }

  // Quick search buttons
  document.querySelectorAll('.ds-quick').forEach(function(btn){
    btn.addEventListener('click', function(){
      const q = this.getAttribute('data-query') || '';
      const qEl = document.getElementById('query');
      if (qEl) qEl.value = q;
      const form = document.getElementById('dual-form');
      if (form) form.dispatchEvent(new Event('submit'));
    });
  });

  // Render helpers
  function renderSummaries(container, summaries) {
    if (!container) return;
    container.innerHTML = '';
    const names = {word2vec:'Word2Vec', fasttext:'FastText', glove:'GloVe'};
    Object.keys(summaries || {}).forEach(function(key){
      const s = summaries[key] || {total:0, top_refs:[]};
      const col = document.createElement('div');
      col.className = 'col-md-4 mb-3';
      col.innerHTML = "\
      <div class=\"card h-100\">\n\
        <div class=\"card-header\"><strong>Ringkasan " + (names[key] || key) + "</strong></div>\n\
        <div class=\"card-body\">\n\
          <div class=\"mb-2\">Total hasil: <span class=\"badge bg-secondary\">" + (s.total||0) + "</span></div>\n\
          " + ((s.top_refs && s.top_refs.length)
            ? "<div><div class=\"text-muted mb-1\">Top " + s.top_refs.length + " (format Qs.X:Y):</div>\n\
                <div>" + s.top_refs.map(function(r){ return "<span class='badge bg-light text-dark me-1 mb-1'>" + r + "</span>"; }).join('') + "</div>\n\
               </div>"
            : "<div class='text-muted'>Tidak ada hasil.</div>") + "\n\
        </div>\n\
      </div>";
      container.appendChild(col);
    });
  }

  function renderResults(tbody, results) {
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!results || !results.length) {
      tbody.innerHTML = "<tr><td colspan=\"6\" class=\"text-center\">Tidak ada hasil ditemukan.</td></tr>";
      return;
    }
    results.forEach(function(it, idx){
      const tr = document.createElement('tr');
      tr.innerHTML = "\
        <td>" + (idx+1) + "</td>\n\
        <td>" + (it.surah_name || it.surah_number) + "</td>\n\
        <td>" + (it.ayat_number || '') + "</td>\n\
        <td style=\"font-family:'Amiri', serif; font-size:1.1rem;\">" + (it.arabic || '') + "</td>\n\
        <td>" + (it.translation || '') + "</td>\n\
        <td><span class=\"badge bg-primary\">" + ((it.similarity||0).toFixed(3)) + "</span></td>";
      tbody.appendChild(tr);
    });
  }

  // AJAX submit
  const form = document.getElementById('dual-form');
  const loading = document.getElementById('ds-loading');
  const summariesDiv = document.getElementById('model-summaries');
  const resultsBody = document.getElementById('dual-results-body');
  if (form) {
    form.addEventListener('submit', function(e){
      e.preventDefault();
      if (loading) loading.style.display = 'block';
      if (summariesDiv) summariesDiv.innerHTML = '';
      if (resultsBody) resultsBody.innerHTML = '';
      const payload = {
        query: document.getElementById('query').value,
        combo: document.getElementById('combo').value,
        limit: document.getElementById('limit').value,
        threshold: document.getElementById('threshold').value,
        require_both: document.getElementById('require_both').checked,
        voting_bonus: document.getElementById('voting_bonus').value,
        a_weight: document.getElementById('a_weight').value,
        b_weight: document.getElementById('b_weight').value,
        method: document.getElementById('method').value,
        use_voting_filter: document.getElementById('use_voting_filter').checked,
        w2v_weight: document.getElementById('w2v_weight').value,
        ft_weight: document.getElementById('ft_weight').value,
        glove_weight: document.getElementById('glove_weight').value
      };
      const apiUrl = form.getAttribute('data-api-url');
      fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(function(res){ return res.json(); })
      .then(function(res){
        if (loading) loading.style.display = 'none';
        if (!res.success) throw new Error(res.message || 'Gagal mengambil hasil');
        const data = res.data || {};
        renderSummaries(summariesDiv, data.model_summaries);
        renderResults(resultsBody, data.results);
      })
      .catch(function(err){
        if (loading) loading.style.display = 'none';
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger mt-3';
        alert.innerText = err.message || 'Terjadi kesalahan.';
        form.parentNode.insertBefore(alert, form.nextSibling);
        setTimeout(function(){ alert.remove(); }, 4000);
      });
    });
  }
})();
