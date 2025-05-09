/**
 * Animations for Elder Care Admin Interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add animation classes to elements
    addAnimations();
    
    // Initialize page transition animations
    initPageTransitions();
    
    // Add hover animations
    addHoverEffects();
});

/**
 * Add animation classes to elements
 */
function addAnimations() {
    // Animate cards with staggered delay
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        const delay = Math.min(index, 5); // Max 5 delays
        card.classList.add('animate-fade-in', `delay-${delay}`);
    });
    
    // Animate table rows with staggered delay
    const tableRows = document.querySelectorAll('.admin-table tbody tr');
    tableRows.forEach((row, index) => {
        const delay = Math.min(index % 5, 4) + 1; // Cycle through delays 1-5
        row.classList.add('animate-slide-in-right', `delay-${delay}`);
    });
    
    // Animate headings
    const headings = document.querySelectorAll('h1, h2, h3, .card-header h5');
    headings.forEach(heading => {
        heading.classList.add('animate-slide-in-up', 'delay-1');
    });
    
    // Animate sidebar items
    const sidebarItems = document.querySelectorAll('.sidebar .nav-link');
    sidebarItems.forEach((item, index) => {
        const delay = Math.min(index % 5, 4) + 1; // Cycle through delays 1-5
        item.classList.add('animate-slide-in-right', `delay-${delay}`);
    });
    
    // Animate logo
    const logo = document.querySelector('.navbar-brand');
    if (logo) {
        logo.classList.add('logo-animate');
    }
}

/**
 * Initialize page transition animations
 */
function initPageTransitions() {
    // Add smooth transition when clicking links
    const contentLinks = document.querySelectorAll('a:not([target="_blank"])');
    
    contentLinks.forEach(link => {
        // Skip links with # or javascript: or mailto:
        if (link.getAttribute('href') && 
            !link.getAttribute('href').startsWith('#') && 
            !link.getAttribute('href').startsWith('javascript:') && 
            !link.getAttribute('href').startsWith('mailto:')) {
            
            link.addEventListener('click', function(e) {
                // Don't animate if it's a download link or has data-no-animation attribute
                if (link.getAttribute('download') || link.hasAttribute('data-no-animation')) {
                    return;
                }
                
                const mainContent = document.querySelector('main');
                if (mainContent) {
                    e.preventDefault();
                    
                    // Fade out
                    mainContent.style.opacity = '0';
                    mainContent.style.transition = 'opacity 0.3s ease';
                    
                    // Navigate after animation completes
                    setTimeout(() => {
                        window.location.href = link.getAttribute('href');
                    }, 300);
                }
            });
        }
    });
    
    // Fade in content when page loads
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.style.opacity = '0';
        setTimeout(() => {
            mainContent.style.opacity = '1';
            mainContent.style.transition = 'opacity 0.5s ease';
        }, 100);
    }
}

/**
 * Add hover effects to elements
 */
function addHoverEffects() {
    // Add pulse effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
            this.style.transition = 'all 0.3s ease';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
    
    // Add subtle scale effect to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}
