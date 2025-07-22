document.addEventListener('DOMContentLoaded', function() {
  const tableBody = document.getElementById('history-table-body');
  const loadingIndicator = document.getElementById('loading-indicator');
  const noDataMessage = document.getElementById('no-data-message');
  const errorMessage = document.getElementById('error-message');
  const filterNama = document.getElementById('filter-nama');
  const filterSurah = document.getElementById('filter-surah');
  const filterTanggal = document.getElementById('filter-tanggal');
  const btnApplyFilter = document.getElementById('btn-apply-filter');
  const btnResetFilter = document.getElementById('btn-reset-filter');

  // Fetch daftar surah untuk filter
  fetch('/api/asr_quran/surah')
    .then(res => res.json())
    .then(data => {
      data.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.nama_arab;
        opt.textContent = `${s.nama_latin} (${s.nama_arab})`;
        filterSurah.appendChild(opt);
      });
    })
    .catch(err => {
      console.error('Error fetching surah list:', err);
    });

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

  // Fungsi untuk memfilter data
  function filterData(data) {
    const namaFilter = filterNama.value.toLowerCase();
    const surahFilter = filterSurah.value;
    const tanggalFilter = filterTanggal.value;
    
    return data.filter(item => {
      // Filter berdasarkan nama
      if (namaFilter && !item.nama_user.toLowerCase().includes(namaFilter)) {
        return false;
      }
      
      // Filter berdasarkan surah
      if (surahFilter && item.surah !== surahFilter) {
        return false;
      }
      
      // Filter berdasarkan tanggal
      if (tanggalFilter) {
        const itemDate = new Date(item.waktu).toISOString().split('T')[0];
        if (itemDate !== tanggalFilter) {
          return false;
        }
      }
      
      return true;
    });
  }

  // Fungsi untuk menampilkan data dalam tabel
  function renderTable(data) {
    tableBody.innerHTML = '';
    
    if (data.length === 0) {
      noDataMessage.style.display = 'block';
      return;
    }
    
    noDataMessage.style.display = 'none';
    
    data.forEach((item, index) => {
      const row = document.createElement('tr');
      
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${item.nama_user}</td>
        <td>${formatDate(item.waktu)}</td>
        <td>${item.surah}</td>
        <td>${item.ayat}</td>
        <td>${item.skor}</td>
        <td>
          <a href="/asr_quran/detail/${item.id}" class="btn btn-sm btn-primary">Detail</a>
        </td>
      `;
      
      tableBody.appendChild(row);
    });
  }

  // Fungsi untuk memuat data riwayat
  function loadHistoryData() {
    loadingIndicator.style.display = 'block';
    noDataMessage.style.display = 'none';
    errorMessage.style.display = 'none';
    
    fetch('/api/asr_quran/riwayat')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        loadingIndicator.style.display = 'none';
        const filteredData = filterData(data);
        renderTable(filteredData);
      })
      .catch(error => {
        loadingIndicator.style.display = 'none';
        errorMessage.textContent = `Error: ${error.message}`;
        errorMessage.style.display = 'block';
      });
  }

  // Event listener untuk tombol filter
  btnApplyFilter.addEventListener('click', function() {
    loadHistoryData();
  });

  // Event listener untuk tombol reset filter
  btnResetFilter.addEventListener('click', function() {
    filterNama.value = '';
    filterSurah.value = '';
    filterTanggal.value = '';
    loadHistoryData();
  });

  // Load data saat halaman dimuat
  loadHistoryData();
});