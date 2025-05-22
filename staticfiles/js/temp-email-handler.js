document.addEventListener('DOMContentLoaded', function() {
    function hideTempMailIcons() {
        // Target all email inputs
        const emailInputs = document.querySelectorAll('input[type="email"]');
        
        emailInputs.forEach(emailInput => {
            // Add email-wrapper class to parent if it doesn't exist
            const wrapper = emailInput.closest('.input-group') || emailInput.parentElement;
            if (!wrapper.classList.contains('email-wrapper')) {
                wrapper.classList.add('email-wrapper');
            }
            
            // Remove suspicious elements
            wrapper.querySelectorAll(
                'img, button, div, span, [data-temp-mail-org], ' +
                '.temp-mail-btn, [class*="temp"], [id*="temp"], ' +
                '[src*="temp-mail"], [src*="tempmail"], ' +
                '[alt*="temp"], [title*="temp"]'
            ).forEach(el => {
                if (!el.matches('input[type="email"]')) {
                    el.remove();
                }
            });
            
            // Add CSS to prevent extension buttons
            const style = document.createElement('style');
            style.textContent = `
                /* Hide temp email extension buttons */
                .email-wrapper [data-temp-mail-org],
                .email-wrapper .temp-mail-btn,
                .email-wrapper [class*="temp"],
                .email-wrapper [id*="temp"] {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    width: 0 !important;
                    height: 0 !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    border: none !important;
                }
                /* Ensure input takes full width */
                .email-wrapper input[type="email"] {
                    flex: 1;
                    min-width: 0;
                }
            `;
            document.head.appendChild(style);
        });
    }

    // Run on load and periodically to catch late-injected elements
    hideTempMailIcons();
    
    let tries = 0;
    const maxTries = 10; // Run for 5 seconds (10 * 500ms)
    const interval = setInterval(() => {
        hideTempMailIcons();
        tries++;
        if (tries >= maxTries) clearInterval(interval);
    }, 500);
    
    // Also run when the form gains focus
    document.addEventListener('focusin', function(e) {
        if (e.target.matches('input[type="email"]')) {
            hideTempMailIcons();
        }
    }, true);
});
