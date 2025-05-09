// main.js - Common JavaScript functions for the Elderly Care Hub

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Real-time clock functionality
    const clockElement = document.getElementById('real-time-clock');
    if (clockElement) {
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    // Remove all spinners that might be showing
    const spinners = document.querySelectorAll('.spinner-border, .spinner-grow, [data-app-spinner="true"], .loading-spinner, .spinner-container, #global-spinner-container');
    spinners.forEach(spinner => {
        spinner.remove();
    });
});

// Update the real-time clock
function updateClock() {
    const clockElement = document.getElementById('real-time-clock');
    if (clockElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        clockElement.textContent = timeString;
    }
}

// Remove the spinner functions and AJAX spinner code

// Remove all page loading overlay related code


