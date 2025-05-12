// Skip to main content accessibility feature

document.addEventListener('DOMContentLoaded', function() {
    var skipLink = document.getElementById('skip-link');
    if (skipLink) {
        skipLink.addEventListener('click', function(event) {
            event.preventDefault();
            var mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.focus();
            }
        });
    }
});
