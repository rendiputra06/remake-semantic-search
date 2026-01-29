/**
 * Chart Module for Evaluation V3
 * Handles Chart.js visualization
 */

export const chartManager = {
    instance: null,

    render(data) {
        const results = data.results.filter((r) => !r.error);
        const labels = results.map((r) => r.label);
        const precision = results.map((r) => r.precision * 100);
        const recall = results.map((r) => r.recall * 100);
        const f1 = results.map((r) => r.f1 * 100);

        if (this.instance) {
            this.instance.destroy();
        }

        const container = document.getElementById('evaluasi-chart');
        container.innerHTML = '<canvas id="evaluasi-chart-canvas"></canvas>';
        const ctx = document.getElementById('evaluasi-chart-canvas').getContext('2d');

        this.instance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Precision (%)",
                        data: precision,
                        backgroundColor: "rgba(40, 167, 69, 0.7)",
                        borderColor: "rgba(40, 167, 69, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Recall (%)",
                        data: recall,
                        backgroundColor: "rgba(23, 162, 184, 0.7)",
                        borderColor: "rgba(23, 162, 184, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "F1-Score (%)",
                        data: f1,
                        backgroundColor: "rgba(255, 193, 7, 0.7)",
                        borderColor: "rgba(255, 193, 7, 1)",
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: { display: true, text: 'Score (%)' }
                    },
                },
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Comparison of Evaluation Metrics' }
                }
            },
        });
    }
};
