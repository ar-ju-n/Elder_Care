/**
 * Custom Admin JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle sidebar toggle on mobile
    const sidebarToggle = document.querySelector('[data-bs-target="#sidebarMenu"]');
    const sidebar = document.getElementById('sidebarMenu');
    
    if (sidebarToggle && sidebar) {
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            const isClickInside = sidebar.contains(event.target) || sidebarToggle.contains(event.target);
            
            if (!isClickInside && window.innerWidth < 768 && sidebar.classList.contains('show')) {
                const bsCollapse = new bootstrap.Collapse(sidebar);
                bsCollapse.hide();
            }
        });
        
        // Close sidebar when clicking on a link on mobile
        const sidebarLinks = sidebar.querySelectorAll('.nav-link');
        sidebarLinks.forEach(link => {
            if (!link.getAttribute('data-bs-toggle')) {
                link.addEventListener('click', function() {
                    if (window.innerWidth < 768 && sidebar.classList.contains('show')) {
                        const bsCollapse = new bootstrap.Collapse(sidebar);
                        bsCollapse.hide();
                    }
                });
            }
        });
    }
    
    // Highlight current section in sidebar
    const currentPath = window.location.pathname;
    const sidebarNavLinks = document.querySelectorAll('.sidebar .nav-link');
    
    sidebarNavLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/custom_admin/') {
            link.classList.add('active');
            
            // If it's in a collapse, expand the parent
            const parentCollapse = link.closest('.collapse');
            if (parentCollapse) {
                parentCollapse.classList.add('show');
                const parentToggle = document.querySelector(`[data-bs-target="#${parentCollapse.id}"]`);
                if (parentToggle) {
                    parentToggle.setAttribute('aria-expanded', 'true');
                }
            }
        }
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle bulk selection
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        const checkboxes = document.querySelectorAll('.object-checkbox');
        
        selectAllCheckbox.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBulkActionButtons();
        });
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateBulkActionButtons();
                // Update select all checkbox
                selectAllCheckbox.checked = [...checkboxes].every(c => c.checked);
                selectAllCheckbox.indeterminate = !selectAllCheckbox.checked && 
                                                 [...checkboxes].some(c => c.checked);
            });
        });
        
        function updateBulkActionButtons() {
            const bulkActionButtons = document.querySelectorAll('.bulk-action');
            const anyChecked = [...checkboxes].some(c => c.checked);
            
            bulkActionButtons.forEach(button => {
                button.disabled = !anyChecked;
                if (anyChecked) {
                    button.classList.remove('disabled');
                } else {
                    button.classList.add('disabled');
                }
            });
        }
    }

    // Handle filter form
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const inputs = filterForm.querySelectorAll('input:not([type=submit]), select');
                inputs.forEach(input => {
                    input.value = '';
                });
                filterForm.submit();
            });
        }
    }

    // Add confirm dialog to delete buttons
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
