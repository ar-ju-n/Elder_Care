/**
 * Dark Mode Functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get the theme toggle button
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    if (!themeToggleBtn) return;
    
    // Function to set theme
    function setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('admin-theme', theme);
        updateTableHeaders(theme);
    }
    
    // Function to explicitly update table headers for dark mode
    function updateTableHeaders(theme) {
        // First, handle all table headers
        const tableHeaders = document.querySelectorAll('table th');
        
        if (theme === 'dark') {
            // Apply dark mode styles
            tableHeaders.forEach(header => {
                header.style.setProperty('background-color', '#343a40', 'important');
                header.style.setProperty('color', '#e3e3e3', 'important');
                header.style.setProperty('border-color', '#495057', 'important');
            });
            
            // Also handle thead elements
            document.querySelectorAll('thead').forEach(thead => {
                thead.style.setProperty('background-color', '#343a40', 'important');
                thead.style.setProperty('color', '#e3e3e3', 'important');
            });
            
            // Handle thead rows
            document.querySelectorAll('thead tr').forEach(tr => {
                tr.style.setProperty('background-color', '#343a40', 'important');
                tr.style.setProperty('color', '#e3e3e3', 'important');
            });
        } else {
            // Remove inline styles for light mode
            tableHeaders.forEach(header => {
                header.style.removeProperty('background-color');
                header.style.removeProperty('color');
                header.style.removeProperty('border-color');
            });
            
            document.querySelectorAll('thead').forEach(thead => {
                thead.style.removeProperty('background-color');
                thead.style.removeProperty('color');
            });
            
            document.querySelectorAll('thead tr').forEach(tr => {
                tr.style.removeProperty('background-color');
                tr.style.removeProperty('color');
            });
        }
    }
    
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('admin-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply theme on page load
    const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    setTheme(initialTheme);
    
    // Also explicitly call updateTableHeaders on page load to ensure tables are styled correctly
    document.addEventListener('DOMContentLoaded', function() {
        updateTableHeaders(initialTheme);
    });
    
    // Update button icon based on current theme
    function updateThemeIcon() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        if (currentTheme === 'dark') {
            themeToggleBtn.setAttribute('title', 'Switch to light mode');
        } else {
            themeToggleBtn.setAttribute('title', 'Switch to dark mode');
        }
    }
    
    // Initialize icon
    updateThemeIcon();
    
    // Toggle theme when button is clicked
    themeToggleBtn.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        setTheme(newTheme);
        updateThemeIcon();
    });
});
