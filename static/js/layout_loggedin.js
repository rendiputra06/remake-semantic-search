// Toggle sidebar for small screens
function toggleSidebar() {
  document.body.classList.toggle('sidebar-shown');
}

// Close sidebar when clicking outside on small screens
(function () {
  document.addEventListener('click', function (e) {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const isSmall = window.matchMedia('(max-width: 991.98px)').matches;
    if (!isSmall) return;
    if (!sidebar) return;

    const clickInsideSidebar = sidebar.contains(e.target);
    const clickOnToggle = toggleBtn && toggleBtn.contains(e.target);

    if (!clickInsideSidebar && !clickOnToggle && document.body.classList.contains('sidebar-shown')) {
      document.body.classList.remove('sidebar-shown');
    }
  });
})();
