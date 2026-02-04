/**
 * API Module for Integrated Evaluation
 * Handles all fetch requests to the backend
 */

export const api = {
    async getQueries() {
        const res = await fetch("/api/query");
        return await res.json();
    },

    async addQuery(text) {
        const res = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        return await res.json();
    },

    async updateQuery(id, text) {
        const res = await fetch(`/api/query/${id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        return await res.json();
    },

    async deleteQuery(id) {
        const res = await fetch(`/api/query/${id}`, { method: "DELETE" });
        return await res.json();
    },

    async getRelevantVerses(queryId) {
        const res = await fetch(`/api/query/${queryId}/relevant_verses`);
        return await res.json();
    },

    async addRelevantVerse(queryId, verseRef) {
        const res = await fetch(`/api/query/${queryId}/relevant_verses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ verse_ref: verseRef }),
        });
        return await res.json();
    },

    async deleteRelevantVerse(id) {
        const res = await fetch(`/api/query/relevant_verse/${id}`, { method: "DELETE" });
        return await res.json();
    },

    async getAyatDetail(surah, ayat) {
        const res = await fetch(`/api/quran/ayat_detail?surah=${surah}&ayat=${ayat}`);
        return await res.json();
    },

    async runEvaluation(queryId, payload) {
        const res = await fetch(`/api/evaluation_v4/${queryId}/run`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        return await res.json();
    }
};
