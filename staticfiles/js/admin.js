// Admin Panel JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const adminSidebar = document.querySelector('.admin-sidebar');
  const adminContent = document.querySelector('.admin-content');
  
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
      adminSidebar.classList.toggle('show');
      adminContent.classList.toggle('sidebar-show');
    });
  }
  
  // Confirm Action
  const confirmActions = document.querySelectorAll('.confirm-action');
  confirmActions.forEach(function(element) {
    element.addEventListener('click', function(e) {
      const confirmMessage = this.getAttribute('data-confirm-message') || 'Are you sure you want to perform this action?';
      if (!confirm(confirmMessage)) {
        e.preventDefault();
      }
    });
  });
  
  // Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Date Range Picker (if available)
  if (typeof daterangepicker !== 'undefined') {
    const dateRangePickers = document.querySelectorAll('.date-range-picker');
    dateRangePickers.forEach(function(element) {
      const options = {
        opens: 'left',
        autoUpdateInput: false,
        locale: {
          cancelLabel: 'Clear',
          applyLabel: 'Apply',
          format: 'YYYY-MM-DD'
        }
      };
      
      new daterangepicker(element, options);
      
      element.addEventListener('apply.daterangepicker', function(ev, picker) {
        element.value = picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD');
      });
      
      element.addEventListener('cancel.daterangepicker', function() {
        element.value = '';
      });
    });
  }
  
  // File Input
  const customFileInputs = document.querySelectorAll('.custom-file-input');
  customFileInputs.forEach(function(element) {
    element.addEventListener('change', function() {
      const fileName = this.files[0].name;
      const nextSibling = this.nextElementSibling;
      nextSibling.innerText = fileName;
    });
  });
  
  // Select All Checkboxes
  const selectAllCheckbox = document.getElementById('selectAll');
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function() {
      const checkboxes = document.querySelectorAll('.item-checkbox');
      checkboxes.forEach(function(checkbox) {
        checkbox.checked = selectAllCheckbox.checked;
      });
      
      // Update bulk actions visibility
      updateBulkActionsVisibility();
    });
    
    // Individual checkboxes
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    itemCheckboxes.forEach(function(checkbox) {
      checkbox.addEventListener('change', function() {
        // Update "select all" checkbox
        const allChecked = document.querySelectorAll('.item-checkbox:checked').length === itemCheckboxes.length;
        selectAllCheckbox.checked = allChecked;
        
        // Update bulk actions visibility
        updateBulkActionsVisibility();
      });
    });
    
    // Function to update bulk actions visibility
    function updateBulkActionsVisibility() {
      const bulkActionsContainer = document.querySelector('.bulk-actions');
      if (bulkActionsContainer) {
        const anyChecked = document.querySelectorAll('.item-checkbox:checked').length > 0;
        bulkActionsContainer.style.display = anyChecked ? 'block' : 'none';
      }
    }
    
    // Initial check
    updateBulkActionsVisibility();
  }
  
  // Form validation
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(function(form) {
    form.addEventListener('submit', function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });
});

