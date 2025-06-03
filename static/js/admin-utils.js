/**
 * Common utilities for admin panel
 */

// Show alert message
function showAlert(type, message) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

  document
    .querySelector(".container")
    .insertBefore(alertDiv, document.querySelector(".container").firstChild);

  // Auto close after 5 seconds
  setTimeout(() => {
    const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
    alert.close();
  }, 5000);
}
