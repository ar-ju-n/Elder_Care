/**
 * Utility functions for Elder Care application
 */

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - Time to wait in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format date to a readable string
 * @param {string|Date} date - Date string or Date object
 * @param {string} locale - Locale string (default: 'en-US')
 * @returns {string} Formatted date string
 */
function formatDate(date, locale = 'en-US') {
    if (!date) return '';
    
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return new Date(date).toLocaleDateString(locale, options);
}

/**
 * Format a number as currency
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (default: 'USD')
 * @param {string} locale - Locale string (default: 'en-US')
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Toggle password visibility
 * @param {string} inputId - The ID of the password input element
 * @param {string} toggleId - The ID of the toggle button element
 */
function togglePasswordVisibility(inputId, toggleId) {
    const passwordInput = document.getElementById(inputId);
    const toggleBtn = document.getElementById(toggleId);
    
    if (!passwordInput || !toggleBtn) return;
    
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // Toggle icon
    const icon = toggleBtn.querySelector('i');
    if (icon) {
        icon.classList.toggle('bi-eye');
        icon.classList.toggle('bi-eye-slash');
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - The text to copy
 * @param {HTMLElement} [button] - Optional button element to show feedback on
 * @returns {Promise<void>}
 */
async function copyToClipboard(text, button = null) {
    try {
        await navigator.clipboard.writeText(text);
        
        if (button) {
            const originalHtml = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check"></i> Copied!';
            button.disabled = true;
            
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.disabled = false;
            }, 2000);
        }
        
        return true;
    } catch (err) {
        console.error('Failed to copy text: ', err);
        return false;
    }
}

/**
 * Get URL parameters
 * @returns {Object} Object containing URL parameters
 */
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    
    for (const [key, value] of params.entries()) {
        result[key] = value;
    }
    
    return result;
}

/**
 * Update URL parameters without page reload
 * @param {Object} params - Object with key-value pairs to update in URL
 * @param {boolean} replace - Whether to replace the current history state
 */
function updateUrlParams(params, replace = false) {
    const url = new URL(window.location);
    
    Object.entries(params).forEach(([key, value]) => {
        if (value === null || value === undefined) {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
    });
    
    if (replace) {
        window.history.replaceState({}, '', url);
    } else {
        window.history.pushState({}, '', url);
    }
}

// Export functions to global scope
window.ElderCare = window.ElderCare || {};
window.ElderCare.Utils = {
    debounce,
    formatDate,
    formatCurrency,
    togglePasswordVisibility,
    copyToClipboard,
    getUrlParams,
    updateUrlParams
};
