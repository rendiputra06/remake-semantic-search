import { api } from '../evaluasi_v4/api.js';

/**
 * Evaluation V5 - Batch Runner
 * Handles sequential async execution and progress reporting
 */
export const runner = {
    async executeSequential(query, rowElements, onProgress) {
        for (let i = 0; i < rowElements.length; i++) {
            const row = rowElements[i];

            // 1. Mark as running
            onProgress(row, 10);

            try {
                // 2. Prepare Payload
                const w2v = parseFloat(row.querySelector('[data-type="w2v"]').value) || 0.5;
                const ft = parseFloat(row.querySelector('[data-type="ft"]').value) || 0.5;
                const gv = parseFloat(row.querySelector('[data-type="gv"]').value) || 0.5;

                const payload = {
                    query_text: query.text,
                    result_limit: 10,
                    selected_methods: ['ensemble'],
                    ensemble_config: {
                        method: 'weighted',
                        w2v_threshold: w2v,
                        ft_threshold: ft,
                        glove_threshold: gv,
                        voting_bonus: 0.05,
                        use_voting_filter: false
                    },
                    threshold_per_model: {
                        ensemble: 0.5,
                        word2vec: w2v,
                        fasttext: ft,
                        glove: gv
                    }
                };

                onProgress(row, 30);

                // 3. Call API
                const resp = await api.runEvaluation(query.id, payload);

                onProgress(row, 80);

                if (resp.success && resp.results) {
                    // Find the ensemble result
                    const ensembleRes = resp.results.find(r => r.method.startsWith('ensemble'));
                    onProgress(row, 100, ensembleRes);
                } else {
                    throw new Error(resp.message || 'Gagal mengambil hasil');
                }

            } catch (err) {
                console.error(`Row ${i + 1} failed:`, err);
                onProgress(row, 100, { error: true });
            }

            // Small artificial delay for visual feedback if results are too fast
            await new Promise(r => setTimeout(r, 200));
        }
    }
};
