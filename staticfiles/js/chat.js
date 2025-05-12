// Remove any unnecessary loading spinners
document.addEventListener('DOMContentLoaded', function() {
    // Remove any loading spinners that might be showing
    const spinners = document.querySelectorAll('.loading-spinner');
    spinners.forEach(spinner => {
        spinner.remove();
    });
    
    // Rest of your chat.js code...
});