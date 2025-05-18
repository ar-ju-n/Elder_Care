// Navbar-specific JS for Elder Care

// Navbar JS for Elder Care (Bootstrap 5)
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme toggle tooltip
    var themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn && window.bootstrap) {
        new bootstrap.Tooltip(themeToggleBtn);
    }
    // Explicitly initialize all dropdowns
    if (window.bootstrap) {
        document.querySelectorAll('.dropdown-toggle').forEach(function(el) {
            new bootstrap.Dropdown(el);
        });
    }
    // Notification bell: let Bootstrap handle dropdown (no manual toggle needed)
    // If you want to show notifications dynamically, use AJAX to fill the dropdown-menu
});
