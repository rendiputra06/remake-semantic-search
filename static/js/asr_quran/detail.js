document.addEventListener('DOMContentLoaded', function() {
  const loadingIndicator = document.getElementById('loading-indicator');
  const errorMessage = document.getElementById('error-message');
  const detailContent = document.getElementById('detail-content');
  
  // Get the ID from the URL
  const pathParts = window.location.pathname.split('/');
  const recordId = pathParts[pathParts.length - 1];
  
  // Fungsi untuk memformat tanggal
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('id-ID', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  // Fetch detail data
  function loadDetailData() {
    loadingIndicator.style.display = 'block';
    detailContent.style.display = 'none';
    errorMessage.style.display = 'none';
    
    fetch(`/api/asr_quran/riwayat/${recordId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        loadingIndicator.style.display = 'none';
        displayDetailData(data);
        detailContent.style.display = 'block';
      })
      .catch(error => {
        loadingIndicator.style.display = 'none';
        errorMessage.textContent = `Error: ${error.message}`;
        errorMessage.style.display = 'block';
      });
  }
  
  // Display detail data
  function displayDetailData(data) {
    // Set basic information
    document.getElementById('detail-nama').textContent = data.nama_user || '';
    document.getElementById('detail-waktu').textContent = formatDate(data.waktu) || '';
    document.getElementById('detail-surah').textContent = data.surah || '';
    document.getElementById('detail-ayat').textContent = data.ayat || '';
    document.getElementById('detail-skor').textContent = data.skor || '';
    
    // Set audio source if available
    const audioElement = document.getElementById('detail-audio');
    if (data.audio_url) {
      audioElement.src = data.audio_url;
    }
    
    // Set reference ayat and transcript
    document.getElementById('detail-ayat-referensi').textContent = data.ayat_referensi || '';
    document.getElementById('detail-transcript').textContent = data.transcript || '';
    
    // Render highlight comparison
    const highlightDiv = document.getElementById('detail-highlight');
    highlightDiv.innerHTML = '';
    
    if (Array.isArray(data.highlight)) {
      data.highlight.forEach(h => {
        const span = document.createElement('span');
        span.textContent = h.kata + ' ';
        
        // Apply appropriate styling based on status
        if (h.status === 'benar') {
          span.className = 'badge bg-success';
        } else if (h.status === 'salah') {
          span.className = 'badge bg-danger';
        } else {
          span.className = 'badge bg-warning text-dark'; // For 'tambahan' or other statuses
        }
        
        highlightDiv.appendChild(span);
      });
    }
  }
  
  // Load data when page loads
  loadDetailData();
});