/**
 * Main JavaScript file for Elder Care application
 * Handles common functionality across all pages
 */

// Import utilities
import { Utils } from './utils.js';
import { FormHandler } from './form-handler.js';

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initBootstrapComponents();
    
    // Initialize form handlers
    initForms();
    
    // Initialize other common components
    initCommonComponents();

    // Initialize dynamic messages dropdown if present
    initNavbarMessagesDropdown();
    
    // Dispatch custom event when initialization is complete
    document.dispatchEvent(new CustomEvent('eldercare:ready'));
});

function initNavbarMessagesDropdown() {
    const dropdown = document.getElementById('messagesDropdown');
    const badge = document.getElementById('messagesUnreadBadge');
    const listContainer = document.getElementById('messagesListContainer');
    const dropdownMenu = document.getElementById('messagesDropdownMenu');
    if (!dropdown || !badge || !listContainer || !dropdownMenu || !window.isAuthenticated) return;

    // Helper to render message item
    function renderMessageItem(msg) {
        return `<li><a class="dropdown-item d-flex align-items-center p-3${msg.is_read ? '' : ' fw-bold'}" href="/accounts/profile/${msg.sender_id}/?tab=messages">
            <div class="flex-shrink-0 me-3">
                <div class="avatar bg-primary bg-opacity-10 text-primary rounded-circle p-2">
                    <i class="bi bi-person fs-5"></i>
                </div>
            </div>
            <div class="flex-grow-1">
                <div class="d-flex justify-content-between">
                    <h6 class="mb-0">${msg.sender}</h6>
                    <small class="text-muted">${msg.created_at}</small>
                </div>
                <p class="small text-truncate mb-0">${msg.content}</p>
            </div>
        </a></li>`;
    }

    // Fetch and render messages
    function fetchMessages() {
        listContainer.innerHTML = '<li class="text-center py-2 text-muted" id="messagesLoading">Loading...</li>';
        fetch('/accounts/messages/api/recent/', {credentials: 'same-origin'})
            .then(r => r.json())
            .then(data => {
                let unreadCount = 0;
                let html = '';
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        if (!msg.is_read) unreadCount++;
                        html += renderMessageItem(msg);
                    });
                } else {
                    html = '<li class="text-center py-2 text-muted">No messages</li>';
                }
                listContainer.innerHTML = html;
                if (unreadCount > 0) {
                    badge.textContent = unreadCount;
                    badge.style.display = '';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(() => {
                listContainer.innerHTML = '<li class="text-center py-2 text-danger">Failed to load messages</li>';
                badge.style.display = 'none';
            });
    }

    // Mark all as read
    function markMessagesRead() {
        fetch('/accounts/messages/api/mark_read/', {
            method: 'POST',
            headers: {'X-CSRFToken': getCSRFToken()},
            credentials: 'same-origin'
        }).then(() => fetchMessages());
    }

    // CSRF helper
    function getCSRFToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // On dropdown open, fetch and mark as read
    dropdown.addEventListener('show.bs.dropdown', function() {
        fetchMessages();
        markMessagesRead();
    });

    // Also fetch on page load for badge
    fetchMessages();
}


/**
 * Initialize all Bootstrap components
 */
function initBootstrapComponents() {
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(popoverTriggerEl => {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Dropdowns (explicitly initialize to ensure all work)
    const dropdownTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
    dropdownTriggerList.forEach(dropdownTriggerEl => {
        return new bootstrap.Dropdown(dropdownTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible[data-bs-autohide]');
    alerts.forEach(alert => {
        const delay = parseInt(alert.getAttribute('data-bs-delay')) || 5000;
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, delay);
    });
}

/**
 * Initialize form handlers
 */
function initForms() {
    // Initialize AJAX forms
    document.querySelectorAll('form[data-ajax-form]').forEach(form => {
        FormHandler.initAjaxForm(form);
    });
    
    // Initialize client-side validation for forms with 'needs-validation' class
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize other common components
 */
function initCommonComponents() {
    // Initialize any datepickers
    if (typeof flatpickr !== 'undefined') {
        document.querySelectorAll('.datepicker').forEach(dateField => {
            flatpickr(dateField, {
                dateFormat: 'Y-m-d',
                allowInput: true,
                // Add more options as needed
            });
        });
    }
    
    // Add active class to current nav item
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
            
            // If it's in a dropdown, also activate the parent
            const parentItem = link.closest('.dropdown-item');
            if (parentItem) {
                parentItem.classList.add('active');
                
                const dropdownToggle = parentItem.closest('.dropdown').querySelector('.dropdown-toggle');
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                }
            }
        }
    });
}

// Make utilities and handlers available globally
window.ElderCare = window.ElderCare || {};
window.ElderCare.Utils = Utils;
window.ElderCare.FormHandler = FormHandler;

// Add global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    
    // Show error to user if showToast is available
    if (typeof window.showToast === 'function') {
        window.showToast('An unexpected error occurred. Please try again.', 'error');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Show error to user if showToast is available
    if (typeof window.showToast === 'function') {
        const errorMessage = event.reason?.message || 'An unexpected error occurred.';
        window.showToast(errorMessage, 'error');
    }
});
