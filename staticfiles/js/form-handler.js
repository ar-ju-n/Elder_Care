/**
 * Form Handler for Elder Care application
 * Provides consistent form handling, validation, and AJAX submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all forms with data-ajax-form attribute
    document.querySelectorAll('form[data-ajax-form]').forEach(form => {
        initAjaxForm(form);
    });
    
    // Initialize file input previews
    document.querySelectorAll('.custom-file-input').forEach(input => {
        input.addEventListener('change', handleFileInputChange);
    });
    
    // Initialize character counters
    document.querySelectorAll('[data-max-length]').forEach(element => {
        initCharacterCounter(element);
    });
});

/**
 * Initialize an AJAX form
 * @param {HTMLFormElement} form - The form element to initialize
 */
function initAjaxForm(form) {
    if (!form) return;
    
    form.addEventListener('submit', handleFormSubmit);
    
    // Add loading class to submit button
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        form._originalSubmitText = submitBtn.innerHTML;
    }
}

/**
 * Handle form submission
 * @param {Event} e - The submit event
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    const method = form.method.toUpperCase();
    const url = form.action || window.location.href;
    
    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span class="ms-2">Processing...</span>
        `;
    }
    
    try {
        const response = await fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken') || window.csrftoken
            },
            credentials: 'same-origin'
        });
        
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        if (!response.ok) {
            throw new Error(data.message || 'An error occurred');
        }
        
        // Handle successful response
        handleFormSuccess(form, data, response);
        
    } catch (error) {
        // Handle errors
        handleFormError(form, error);
    } finally {
        // Reset button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = form._originalSubmitText || 'Submit';
        }
    }
}

/**
 * Handle successful form submission
 * @param {HTMLFormElement} form - The form element
 * @param {Object|string} data - Response data
 * @param {Response} response - The response object
 */
function handleFormSuccess(form, data, response) {
    // If response contains redirect, navigate to that URL
    if (data.redirect) {
        window.location.href = data.redirect;
        return;
    }
    
    // Show success message
    if (data.message) {
        const messageType = response.ok ? 'success' : 'error';
        if (typeof window.showToast === 'function') {
            window.showToast(data.message, messageType);
        } else {
            alert(data.message);
        }
    }
    
    // Reset form if needed
    if (form.hasAttribute('data-reset-on-success')) {
        form.reset();
    }
    
    // Trigger success event
    const successEvent = new CustomEvent('form:success', { 
        detail: { form, data, response },
        bubbles: true
    });
    form.dispatchEvent(successEvent);
}

/**
 * Handle form submission error
 * @param {HTMLFormElement} form - The form element
 * @param {Error} error - The error object
 */
function handleFormError(form, error) {
    console.error('Form submission error:', error);
    
    const errorMessage = error.message || 'An error occurred while processing your request.';
    
    if (typeof window.showToast === 'function') {
        window.showToast(errorMessage, 'error');
    } else {
        alert(errorMessage);
    }
    
    // Trigger error event
    const errorEvent = new CustomEvent('form:error', { 
        detail: { form, error },
        bubbles: true
    });
    form.dispatchEvent(errorEvent);
}

/**
 * Handle file input change event to show file name
 * @param {Event} e - The change event
 */
function handleFileInputChange(e) {
    const input = e.target;
    const fileName = input.files[0]?.name || 'Choose file';
    const label = input.nextElementSibling;
    
    if (label && label.classList.contains('custom-file-label')) {
        label.textContent = fileName;
    }
}

/**
 * Initialize character counter for text inputs and textareas
 * @param {HTMLElement} element - The input or textarea element
 */
function initCharacterCounter(element) {
    const maxLength = parseInt(element.getAttribute('data-max-length'), 10);
    if (isNaN(maxLength)) return;
    
    const counterId = `char-counter-${Math.random().toString(36).substr(2, 9)}`;
    const counter = document.createElement('small');
    counter.id = counterId;
    counter.className = 'form-text text-muted text-end d-block';
    
    // Insert counter after the element
    element.insertAdjacentElement('afterend', counter);
    
    // Update counter on input
    const updateCounter = () => {
        const remaining = maxLength - (element.value?.length || 0);
        counter.textContent = `${remaining} characters remaining`;
        
        if (remaining < 0) {
            counter.classList.add('text-danger');
            element.classList.add('is-invalid');
        } else {
            counter.classList.remove('text-danger');
            element.classList.remove('is-invalid');
        }
    };
    
    // Initial update
    updateCounter();
    
    // Add event listeners
    element.addEventListener('input', updateCounter);
    element.addEventListener('change', updateCounter);
}

// Export functions to global scope
window.ElderCare = window.ElderCare || {};
window.ElderCare.FormHandler = {
    initAjaxForm,
    handleFormSubmit,
    handleFormSuccess,
    handleFormError,
    handleFileInputChange,
    initCharacterCounter
};
