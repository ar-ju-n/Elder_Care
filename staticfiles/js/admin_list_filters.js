document.addEventListener('DOMContentLoaded', function() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.object-checkbox');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkActionForm = document.getElementById('bulkActionForm');
    
    // Handle select all checkbox
    selectAll.addEventListener('change', function() {
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
        });
        updateBulkDeleteButton();
    });
    
    // Handle individual checkboxes
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkDeleteButton();
            // Update select all checkbox
            selectAll.checked = [...checkboxes].every(c => c.checked);
        });
    });
    
    // Update bulk delete button state
    function updateBulkDeleteButton() {
        const anyChecked = [...checkboxes].some(c => c.checked);
        bulkDeleteBtn.disabled = !anyChecked;
    }
    
    // Handle bulk delete button
    bulkDeleteBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete the selected items?')) {
            bulkActionForm.submit();
        }
    });
});
