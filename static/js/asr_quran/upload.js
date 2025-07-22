document.addEventListener('DOMContentLoaded', function() {
  const surahSelect = document.getElementById('surah');
  const ayatSelect = document.getElementById('ayat');
  const form = document.getElementById('asr-upload-form');
  const resultDiv = document.getElementById('asr-result');
  const errorDiv = document.getElementById('asr-error');

  // Fetch daftar surah
  fetch('/api/asr_quran/surah')
    .then(res => res.json())
    .then(data => {
      data.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = `${s.nama_latin} (${s.nama_arab})`;
        surahSelect.appendChild(opt);
      });
    });

  // Fetch ayat saat surah berubah
  surahSelect.addEventListener('change', function() {
    ayatSelect.innerHTML = '<option value="">Pilih Ayat</option>';
    if (!this.value) return;
    fetch(`/api/asr_quran/ayat?surah_id=${this.value}`)
      .then(res => res.json())
      .then(data => {
        data.forEach(a => {
          const opt = document.createElement('option');
          opt.value = a.id;
          opt.textContent = `${a.nomor_ayat}: ${a.teks_arab}`;
          ayatSelect.appendChild(opt);
        });
      });
  });

  // Handle submit form
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    resultDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    const formData = new FormData(form);
    // Ganti nama field agar sesuai endpoint
    formData.set('audio', formData.get('audio'));
    formData.set('ayat_id', formData.get('ayat'));
    formData.set('nama_user', formData.get('nama_user'));
    fetch('/api/asr_quran/asr/upload', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        errorDiv.textContent = data.error;
        errorDiv.style.display = 'block';
        return;
      }
      document.getElementById('asr-transcript').textContent = data.transcript || '';
      document.getElementById('asr-skor').textContent = data.skor || '';
      document.getElementById('asr-ref').textContent = data.ayat_referensi || '';
      // Render highlight
      const highlightDiv = document.getElementById('asr-highlight');
      highlightDiv.innerHTML = '';
      if (Array.isArray(data.highlight)) {
        data.highlight.forEach(h => {
          const span = document.createElement('span');
          span.textContent = h.kata + ' ';
          if (h.status === 'benar') span.className = 'badge bg-success';
          else if (h.status === 'salah') span.className = 'badge bg-danger';
          else span.className = 'badge bg-warning text-dark';
          highlightDiv.appendChild(span);
        });
      }
      resultDiv.style.display = 'block';
    })
    .catch(err => {
      errorDiv.textContent = err.message || 'Terjadi error.';
      errorDiv.style.display = 'block';
    });
  });
}); 