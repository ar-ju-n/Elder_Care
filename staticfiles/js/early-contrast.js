// This script should be included in the <head> before any other scripts
(function() {
    if (localStorage.getItem('highContrast') === 'on') {
        document.documentElement.classList.add('high-contrast');
        // Set a flag that we can check later
        window.highContrastEnabled = true;
    }
})();