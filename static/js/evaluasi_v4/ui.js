/**
 * UI Module for Evaluation V3
 * Handles common DOM manipulation, spinners, and impact labels
 */

export const ui = {
    showSpinner(el, msg = "Memuat...") {
        el.innerHTML = `<div class='text-center py-3'><div class='spinner-border text-primary' role='status'></div><div>${msg}</div></div>`;
    },

    getImpactLabel(threshold) {
        if (threshold === 0) return "Very Low (Noisy)";
        if (threshold < 0.4) return "Low";
        if (threshold < 0.6) return "Normal";
        if (threshold < 0.8) return "High (Selective)";
        return "Very High (Strict)";
    },

    updateThresholdDisplay(slider, valueDisplay, impactDisplay) {
        const value = parseFloat(slider.value);
        valueDisplay.textContent = value.toFixed(2);
        impactDisplay.textContent = this.getImpactLabel(value);
    },

    formatPercent(val) {
        return (val * 100).toFixed(1) + "%";
    }
};
