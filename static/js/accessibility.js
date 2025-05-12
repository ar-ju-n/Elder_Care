// Accessibility: Font size and contrast toggles

// Apply high contrast mode as early as possible - BEFORE DOMContentLoaded
(function() {
    // Check localStorage before DOM is ready
    if (localStorage.getItem('highContrast') === 'on') {
        // Apply to document.documentElement (html element) immediately
        document.documentElement.classList.add('high-contrast');
    }
})();

document.addEventListener('DOMContentLoaded', function() {
    // Apply high contrast to body if it's enabled in localStorage
    if (localStorage.getItem('highContrast') === 'on') {
        document.body.classList.add('high-contrast');
        // Update button state
        const contrastBtn = document.getElementById('toggle-contrast');
        if (contrastBtn) {
            contrastBtn.setAttribute('aria-pressed', 'true');
        }
    }
    
    const increaseBtn = document.getElementById('increase-font');
    const decreaseBtn = document.getElementById('decrease-font');
    const sizeClasses = ['font-size-default', 'font-size-large', 'font-size-xlarge'];
    let currentIndex = 0;
    function applyFontSize(idx) {
        document.body.classList.remove(...sizeClasses);
        document.body.classList.add(sizeClasses[idx]);
        currentIndex = idx;
    }
    applyFontSize(0);
    if (increaseBtn) {
        increaseBtn.addEventListener('click', function() {
            if (currentIndex < sizeClasses.length - 1) {
                applyFontSize(currentIndex + 1);
            }
        });
    }
    if (decreaseBtn) {
        decreaseBtn.addEventListener('click', function() {
            if (currentIndex > 0) {
                applyFontSize(currentIndex - 1);
            }
        });
    }
    const contrastBtn = document.getElementById('toggle-contrast');
    if (contrastBtn) {
        contrastBtn.addEventListener('click', function() {
            document.documentElement.classList.toggle('high-contrast');
            document.body.classList.toggle('high-contrast');
            
            if (document.body.classList.contains('high-contrast')) {
                localStorage.setItem('highContrast', 'on');
                contrastBtn.setAttribute('aria-pressed', 'true');
            } else {
                localStorage.setItem('highContrast', 'off');
                contrastBtn.setAttribute('aria-pressed', 'false');
            }
        });
    }
});



