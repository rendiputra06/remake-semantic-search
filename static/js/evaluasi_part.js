// Event reset ayat relevan
document.querySelectorAll(".btn-reset-relevant-verses").forEach((btn) => {
    btn.addEventListener("click", function (e) {
        e.stopPropagation();
        const id = this.getAttribute("data-id");
        Swal.fire({
            title: "Reset Ayat Relevan?",
            text: "Seluruh ayat relevan pada query ini akan dihapus. Lanjutkan?",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Ya, Reset",
            cancelButtonText: "Batal",
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire({
                    title: "Mereset ayat relevan...",
                    html: "Mohon tunggu, proses sedang berjalan.",
                    allowOutsideClick: false,
                    didOpen: () => {
                        Swal.showLoading();
                    },
                });
                fetch(`/api/query/${id}/relevant_verses/reset`, {
                    method: "POST",
                })
                    .then((res) =>
                        res
                            .json()
                            .then((data) => ({ status: res.status, data }))
                    )
                    .then(({ status, data }) => {
                        if (status === 200 && data.success) {
                            Swal.fire({
                                icon: "success",
                                title: "Berhasil",
                                text: "Ayat relevan berhasil direset.",
                            });
                            location.reload();
                        } else {
                            Swal.fire({
                                icon: "error",
                                title: "Gagal",
                                text:
                                    data.message || "Gagal reset ayat relevan.",
                            });
                        }
                    })
                    .catch((res) => {
                        console.error("Error:", res);
                        Swal.fire({
                            icon: "error",
                            title: "Gagal",
                            text: "Terjadi kesalahan saat reset.",
                        });
                    });
            }
        });
    });
});
