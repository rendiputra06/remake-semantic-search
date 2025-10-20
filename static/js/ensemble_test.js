/**
 * Ensemble Test Page JavaScript
 * Handles all interactive functionality for the ensemble testing page
 */

class EnsembleTestApp {
    constructor() {
        this.chartInstance = null;
        this.ayatDataMap = {};
        this.initializeComponents();
    }

    initializeComponents() {
        this.initWeightSliders();
        this.initQuickSearch();
        this.initSettingsToggle();
        this.initTheoryToggle();
        this.initFormSubmission();
        this.initModalHandlers();
    }

    // Enhanced weight sliders with impact indicators
    initWeightSliders() {
        ['w2v_weight','ft_weight','glove_weight'].forEach(id => {
            const slider = document.getElementById(id);
            const valueDisplay = document.getElementById(id + '_val');
            const impactDisplay = document.getElementById(id.replace('weight', 'impact'));

            if (!slider || !valueDisplay || !impactDisplay) return;

            function updateWeightDisplay() {
                const value = parseFloat(slider.value);
                valueDisplay.textContent = value.toFixed(1);

                // Update badge color based on value
                valueDisplay.className = 'badge ms-2';
                if (value === 0) {
                    valueDisplay.classList.add('bg-secondary');
                    impactDisplay.textContent = 'Disabled';
                    impactDisplay.parentElement.classList.remove('text-success', 'text-warning', 'text-danger');
                    impactDisplay.parentElement.classList.add('text-muted');
                } else if (value < 0.5) {
                    valueDisplay.classList.add('bg-danger');
                    impactDisplay.textContent = 'Low';
                    impactDisplay.parentElement.classList.remove('text-success', 'text-warning', 'text-muted');
                    impactDisplay.parentElement.classList.add('text-danger');
                } else if (value < 1.5) {
                    valueDisplay.classList.add('bg-warning', 'text-dark');
                    impactDisplay.textContent = 'Normal';
                    impactDisplay.parentElement.classList.remove('text-success', 'text-danger', 'text-muted');
                    impactDisplay.parentElement.classList.add('text-warning');
                } else {
                    valueDisplay.classList.add('bg-success');
                    impactDisplay.textContent = 'High';
                    impactDisplay.parentElement.classList.remove('text-warning', 'text-danger', 'text-muted');
                    impactDisplay.parentElement.classList.add('text-success');
                }
            }

            slider.addEventListener('input', updateWeightDisplay);
            updateWeightDisplay(); // Initial update
        });
    }

    // Fixed quick search functionality
    initQuickSearch() {
        document.querySelectorAll('.quick-search').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const query = button.getAttribute('data-query');
                if (query) {
                    // Fill the query input
                    const queryInput = document.getElementById('query');
                    if (queryInput) {
                        queryInput.value = query;
                        queryInput.focus();
                    }

                    // Submit the form programmatically
                    this.submitForm();
                }
            });
        });
    }

    // Enhanced settings toggle with animation
    initSettingsToggle() {
        const toggleBtn = document.getElementById('toggle-settings');
        if (!toggleBtn) return;

        toggleBtn.addEventListener('click', () => {
            const settingsCard = document.getElementById('additional-settings');
            const icon = toggleBtn.querySelector('i');

            if (!settingsCard) return;

            if (settingsCard.style.display === 'none') {
                settingsCard.style.display = 'block';
                settingsCard.style.animation = 'fadeInUp 0.3s ease-in-out';
                icon.className = 'fas fa-cog me-1 fa-spin';
                toggleBtn.classList.remove('btn-outline-secondary');
                toggleBtn.classList.add('btn-outline-primary');
                toggleBtn.innerHTML = '<i class="fas fa-cog me-1 fa-spin"></i>Sembunyikan Pengaturan';
            } else {
                settingsCard.style.animation = 'fadeOutDown 0.3s ease-in-out';
                setTimeout(() => {
                    settingsCard.style.display = 'none';
                }, 280);
                icon.className = 'fas fa-cog me-1';
                toggleBtn.classList.remove('btn-outline-primary');
                toggleBtn.classList.add('btn-outline-secondary');
                toggleBtn.innerHTML = '<i class="fas fa-cog me-1"></i>Pengaturan Lanjutan';
            }
        });
    }

    // Theory panel toggle
    initTheoryToggle() {
        const theoryPanel = document.getElementById('ensemble-theory');
        const toggleTheoryBtn = document.getElementById('toggle-theory');

        if (!theoryPanel || !toggleTheoryBtn) return;

        toggleTheoryBtn.addEventListener('click', () => {
            if (theoryPanel.style.display === 'none') {
                theoryPanel.style.display = 'block';
                toggleTheoryBtn.innerHTML = '<i class="fas fa-info-circle me-1"></i>Sembunyikan Rumus Ensemble';
            } else {
                theoryPanel.style.display = 'none';
                toggleTheoryBtn.innerHTML = '<i class="fas fa-info-circle me-1"></i>Lihat Rumus Ensemble';
            }
        });
    }

    // Form submission handler
    initFormSubmission() {
        const form = document.getElementById('ensemble-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });
    }

    // Programmatic form submission
    submitForm() {
        const form = document.getElementById('ensemble-form');
        const resultsDiv = document.getElementById('ensemble-results');
        const tableBody = document.getElementById('ensemble-table-body');
        const chartContainer = document.getElementById('chart-container');
        const loadingDiv = document.getElementById('ensemble-loading');
        const summaryDiv = document.getElementById('ensemble-summary');

        if (!form || !resultsDiv || !tableBody || !chartContainer || !loadingDiv || !summaryDiv) {
            console.error('Required form elements not found');
            this.showError('Komponen form tidak ditemukan. Silakan refresh halaman.');
            return;
        }

        // Hide results and show loading
        resultsDiv.style.display = 'none';
        summaryDiv.innerHTML = '';
        tableBody.innerHTML = '';
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }
        chartContainer.innerHTML = '';
        loadingDiv.style.display = 'block';

        // Collect form data
        const formData = new FormData(form);
        const data = {
            query: document.getElementById('query')?.value?.trim() || '',
            method: document.getElementById('method')?.value || 'weighted',
            threshold: parseFloat(document.getElementById('threshold')?.value) || 0.5,
            voting_bonus: parseFloat(document.getElementById('voting_bonus')?.value) || 0.05,
            limit: parseInt(document.getElementById('limit')?.value) || 10,
            w2v_weight: parseFloat(document.getElementById('w2v_weight')?.value) || 1.0,
            ft_weight: parseFloat(document.getElementById('ft_weight')?.value) || 1.0,
            glove_weight: parseFloat(document.getElementById('glove_weight')?.value) || 1.0
        };

        // Validate required fields
        if (!data.query) {
            this.showError('Query tidak boleh kosong');
            loadingDiv.style.display = 'none';
            return;
        }

        if (data.threshold < 0 || data.threshold > 1) {
            this.showError('Threshold harus antara 0 dan 1');
            loadingDiv.style.display = 'none';
            return;
        }

        // Submit to API
        fetch('/api/models/ensemble/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(result => {
            loadingDiv.style.display = 'none';
            if (!result.success) {
                throw new Error(result.message || 'Gagal mengambil hasil ensemble');
            }
            this.renderResults(result.data);
        })
        .catch(error => {
            loadingDiv.style.display = 'none';
            resultsDiv.style.display = 'none';
            tableBody.innerHTML = '';
            chartContainer.innerHTML = '';
            if (this.chartInstance) {
                this.chartInstance.destroy();
            }
            this.showError(error.message || 'Terjadi kesalahan saat menghubungi server.');
        });
    }

    // Render search results
    renderResults(data) {
        const { results, visual_data, total_count } = data;
        const resultsDiv = document.getElementById('ensemble-results');
        const tableBody = document.getElementById('ensemble-table-body');
        const chartContainer = document.getElementById('chart-container');
        const summaryDiv = document.getElementById('ensemble-summary');

        if (!resultsDiv || !tableBody || !chartContainer || !summaryDiv) return;

        this.ayatDataMap = {};

        if (!results || results.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4"><i class="fas fa-search me-2"></i>Tidak ada hasil ditemukan untuk query ini.</td></tr>';
            summaryDiv.innerHTML = '<span class="text-muted">Total hasil: <b>0</b></span>';
            resultsDiv.style.display = 'block';
            return;
        }

        // Calculate summary statistics
        let totalW2V = 0, totalFT = 0, totalGloVe = 0, voting3 = 0, voting2 = 0;
        results.forEach(r => {
            if ((r.individual_scores?.word2vec||0) > 0) totalW2V++;
            if ((r.individual_scores?.fasttext||0) > 0) totalFT++;
            if ((r.individual_scores?.glove||0) > 0) totalGloVe++;
            if (r.model_count === 3) voting3++;
            if (r.model_count === 2) voting2++;
            this.ayatDataMap[r.verse_id] = r;
        });

        // Create summary text
        let summaryText = `<span class="me-3">Total hasil: <b>${total_count || results.length}</b></span>`;
        if ((total_count || results.length) > 100 && document.getElementById('limit')?.value == '0') {
            summaryText += `<span class="me-3 text-danger">Ditampilkan 100 dari ${total_count || results.length} hasil</span>`;
        }
        summaryText += `
            <span class="me-3">Word2Vec: <b>${totalW2V}</b></span>
            <span class="me-3">FastText: <b>${totalFT}</b></span>
            <span class="me-3">GloVe: <b>${totalGloVe}</b></span>
            <span class="me-3">Voting 3: <b>${voting3}</b></span>
            <span class="me-3">Voting 2: <b>${voting2}</b></span>
        `;
        summaryDiv.innerHTML = summaryText;

        // Render table
        tableBody.innerHTML = '';
        results.forEach((r, i) => {
            const row = document.createElement('tr');
            row.className = 'ayat-row';
            row.setAttribute('data-verse-id', r.verse_id);
            row.innerHTML = `
                <td>${i+1}</td>
                <td>${r.surah_name || r.surah_number}</td>
                <td>${r.ayat_number}</td>
                <td><b>${(r.similarity||0).toFixed(3)}</b></td>
                <td>${r.individual_scores?.word2vec?.toFixed(3) ?? '-'}</td>
                <td>${r.individual_scores?.fasttext?.toFixed(3) ?? '-'}</td>
                <td>${r.individual_scores?.glove?.toFixed(3) ?? '-'}</td>
                <td>${r.model_count ?? '-'}</td>
                <td>${r.meta_ensemble_score !== undefined ? r.meta_ensemble_score.toFixed(3) : '-'}</td>
            `;
            tableBody.appendChild(row);
        });

        // Render visualization chart
        this.renderChart(visual_data);

        resultsDiv.style.display = 'block';
    }

    // Render Chart.js visualization
    renderChart(visualData) {
        const chartContainer = document.getElementById('chart-container');
        if (!chartContainer || !visualData || visualData.length === 0) return;

        // Destroy existing chart
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        // Calculate averages
        const avg = arr => arr.reduce((a,b)=>a+b,0)/arr.length;
        const w2v = avg(visualData.map(v=>v.word2vec||0));
        const ft = avg(visualData.map(v=>v.fasttext||0));
        const glove = avg(visualData.map(v=>v.glove||0));
        const ensemble = avg(visualData.map(v=>v.similarity||0));
        const meta = visualData.some(v=>v.meta_ensemble_score!==null) ? avg(visualData.map(v=>v.meta_ensemble_score||0)) : null;

        const labels = ['Word2Vec','FastText','GloVe','Ensemble'];
        const dataArr = [w2v,ft,glove,ensemble];
        if (meta!==null) {
            labels.push('Meta-Ensemble');
            dataArr.push(meta);
        }

        chartContainer.innerHTML = '<canvas id="ensembleChart"></canvas>';
        const ctx = document.getElementById('ensembleChart').getContext('2d');

        // Custom plugin for data labels
        const customDataLabels = {
            id: 'customDataLabels',
            afterDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.font = 'bold 12px Arial';
                ctx.fillStyle = '#000';

                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    chart.getDatasetMeta(datasetIndex).data.forEach((bar, index) => {
                        const data = dataset.data[index];
                        const value = data.toFixed(3);
                        const x = bar.x;
                        const y = bar.y - 5;
                        ctx.fillText(value, x, y);
                    });
                });
            }
        };

        this.chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Rata-rata Skor',
                    data: dataArr,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 99, 132, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(3);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(2);
                            }
                        }
                    }
                }
            },
            plugins: [customDataLabels]
        });
    }

    // Modal handlers for ayat details
    initModalHandlers() {
        $(document).on('click', '.ayat-row', (e) => {
            e.preventDefault();
            const verseId = $(e.currentTarget).data('verse-id');
            const ayat = this.ayatDataMap[verseId];
            if (!ayat) {
                console.warn('Ayat data not found for verse ID:', verseId);
                return;
            }

            let html = `
                <div class="mb-3">
                    <strong><i class="fas fa-book me-2"></i>Surah:</strong> ${ayat.surah_name || ayat.surah_number}
                    &nbsp;&nbsp;
                    <strong><i class="fas fa-quote-left me-2"></i>Ayat:</strong> ${ayat.ayat_number}
                </div>
                <div class="mb-3 p-3 bg-light rounded">
                    <div style="font-family:'Scheherazade',serif;font-size:1.4em; direction: rtl; text-align: right; line-height: 1.8;">
                        ${ayat.arabic || '-'}
                    </div>
                </div>
                <div class="mb-3">
                    <strong><i class="fas fa-language me-2"></i>Terjemahan:</strong><br>
                    <div class="mt-2 p-2 bg-white border rounded">${ayat.translation || '-'}</div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <strong><i class="fas fa-chart-bar me-2"></i>Skor Individual:</strong><br>
                        <small class="text-muted">Word2Vec: <b>${ayat.individual_scores?.word2vec?.toFixed(3) ?? '-'}</b></small><br>
                        <small class="text-muted">FastText: <b>${ayat.individual_scores?.fasttext?.toFixed(3) ?? '-'}</b></small><br>
                        <small class="text-muted">GloVe: <b>${ayat.individual_scores?.glove?.toFixed(3) ?? '-'}</b></small>
                    </div>
                    <div class="col-md-6">
                        <strong><i class="fas fa-calculator me-2"></i>Skor Ensemble:</strong><br>
                        <small class="text-muted">Ensemble: <b>${ayat.similarity?.toFixed(3) ?? '-'}</b></small><br>
                        <small class="text-muted">Voting: <b>${ayat.model_count ?? '-'}</b></small><br>
                        ${ayat.meta_ensemble_score !== undefined ? `<small class="text-muted">Meta-Ensemble: <b>${ayat.meta_ensemble_score?.toFixed(3) ?? '-'}</b></small>` : ''}
                    </div>
                </div>
            `;

            $('#ayat-detail-body').html(html);
            $('#ayatDetailModal').modal('show');
        });
    }

    // Show error message
    showError(message) {
        const form = document.getElementById('ensemble-form');
        if (!form) return;

        // Remove existing error alerts
        form.querySelectorAll('.alert-danger').forEach(existing => existing.remove());

        const alert = document.createElement('div');
        alert.className = 'alert alert-danger mt-3 alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        form.parentNode.insertBefore(alert, form.nextSibling);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ensembleApp = new EnsembleTestApp();
});
