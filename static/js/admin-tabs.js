/**
 * Admin panel tab management
 */
document.addEventListener("DOMContentLoaded", function () {
  // Get tab elements
  const adminTabs = document.getElementById("adminTabs");
  const adminTabsContent = document.getElementById("adminTabsContent");

  if (adminTabs && adminTabsContent) {
    // Handle tab clicks
    adminTabs.addEventListener("click", function (e) {
      const target = e.target;
      if (target.classList.contains("nav-link")) {
        // Save active tab ID to localStorage
        localStorage.setItem("activeAdminTab", target.id);
      }
    });

    // Restore active tab on page load
    const activeTabId = localStorage.getItem("activeAdminTab");
    if (activeTabId) {
      const tabToActivate = document.getElementById(activeTabId);
      if (tabToActivate) {
        const bsTab = new bootstrap.Tab(tabToActivate);
        bsTab.show();
      }
    }

    // Handle linguistic sub-tabs
    const linguisticSubTabs = document.getElementById("linguisticSubTabs");
    if (linguisticSubTabs) {
      linguisticSubTabs.addEventListener("click", function (e) {
        const target = e.target;
        if (target.classList.contains("nav-link")) {
          // Save active linguistic sub-tab ID
          localStorage.setItem("activeLinguisticTab", target.id);
        }
      });

      // Restore active linguistic sub-tab
      const activeLingTabId = localStorage.getItem("activeLinguisticTab");
      if (activeLingTabId) {
        const lingTabToActivate = document.getElementById(activeLingTabId);
        if (lingTabToActivate) {
          const bsTab = new bootstrap.Tab(lingTabToActivate);
          bsTab.show();
        }
      }
    }
  }
});
