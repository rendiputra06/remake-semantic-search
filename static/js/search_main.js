$(document).ready(function () {
  // Add hover effects to cards
  $(".search-card").hover(
    function () {
      $(this).addClass("shadow-lg");
    },
    function () {
      $(this).removeClass("shadow-lg");
    }
  );

  // Add click animation to buttons
  $(".btn").click(function () {
    $(this).addClass("btn-clicked");
    setTimeout(() => {
      $(this).removeClass("btn-clicked");
    }, 200);
  });

  // Add smooth scrolling for anchor links
  $('a[href^="#"]').click(function (e) {
    e.preventDefault();
    const target = $(this.getAttribute("href"));
    if (target.length) {
      $("html, body").animate(
        {
          scrollTop: target.offset().top - 20,
        },
        500
      );
    }
  });

  // Add loading animation for card links
  $(".card-footer .btn").click(function () {
    const btn = $(this);
    const originalText = btn.html();

    btn.html('<i class="fas fa-spinner fa-spin me-2"></i>Memuat...');
    btn.prop("disabled", true);

    // Re-enable after a short delay (in case of navigation issues)
    setTimeout(() => {
      btn.html(originalText);
      btn.prop("disabled", false);
    }, 2000);
  });

  // Add tooltip functionality
  $('[data-bs-toggle="tooltip"]').tooltip();

  // Add animation for table rows
  $(".table tbody tr").hover(
    function () {
      $(this).addClass("table-active");
    },
    function () {
      $(this).removeClass("table-active");
    }
  );

  // Add counter animation for statistics
  animateCounters();
});

function animateCounters() {
  $(".counter").each(function () {
    const $this = $(this);
    const countTo = $this.attr("data-count");

    $({ countNum: $this.text() }).animate(
      {
        countNum: countTo,
      },
      {
        duration: 2000,
        easing: "swing",
        step: function () {
          $this.text(Math.floor(this.countNum));
        },
        complete: function () {
          $this.text(this.countNum);
        },
      }
    );
  });
}

// Add CSS for button click animation
const style = document.createElement("style");
style.textContent = `
    .btn-clicked {
        transform: scale(0.95);
        transition: transform 0.1s ease-in-out;
    }
    
    .search-card {
        transition: all 0.3s ease-in-out;
    }
    
    .search-card:hover {
        transform: translateY(-5px);
    }
    
    .table tbody tr {
        transition: background-color 0.2s ease-in-out;
    }
    
    .card-footer .btn {
        transition: all 0.3s ease-in-out;
    }
    
    .card-footer .btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
`;
document.head.appendChild(style);
