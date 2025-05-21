// Handles populating the Add/Edit Link modal with the correct data for editing

document.addEventListener('DOMContentLoaded', function() {
    const linkModal = document.getElementById('addLinkModal');
    if (!linkModal) return;
    const titleInput = linkModal.querySelector('input[name="title"]');
    const descriptionInput = linkModal.querySelector('textarea[name="description"]');
    const urlInput = linkModal.querySelector('input[name="url"]');
    const form = linkModal.querySelector('form');

    // Reset modal on close
    linkModal.addEventListener('hidden.bs.modal', function () {
        form.reset();
        let hidden = form.querySelector('input[name="edit_link_id"]');
        if (hidden) hidden.remove();
        let addInput = form.querySelector('input[name="add_link"]');
        if (!addInput) {
            addInput = document.createElement('input');
            addInput.type = 'hidden';
            addInput.name = 'add_link';
            addInput.value = '1';
            form.appendChild(addInput);
        }
    });

    // Listen for edit button clicks
    document.querySelectorAll('.edit-link-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            // Set values
            titleInput.value = btn.getAttribute('data-link-title');
            descriptionInput.value = btn.getAttribute('data-link-description');
            urlInput.value = btn.getAttribute('data-link-url');
            // Add hidden input for edit mode
            let editId = btn.getAttribute('data-link-id');
            let hidden = form.querySelector('input[name="edit_link_id"]');
            if (!hidden) {
                hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = 'edit_link_id';
                form.appendChild(hidden);
            }
            hidden.value = editId;
            // Remove add_link input if present
            let addInput = form.querySelector('input[name="add_link"]');
            if (addInput) addInput.remove();
        });
    });
});
