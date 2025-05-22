// Handles populating the Add/Edit Article modal with the correct data for editing

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('addArticleModal');
    const titleInput = document.querySelector('#addArticleModal input[name="title"]');
    const bodyInput = document.querySelector('#addArticleModal textarea[name="body"]');
    const tagsSelect = document.querySelector('#addArticleModal select[name="tags"]');
    const form = document.querySelector('#addArticleModal form');

    // Reset modal on close
    modal.addEventListener('hidden.bs.modal', function () {
        form.reset();
        if (form.querySelector('input[name="edit_article_id"]')) {
            form.querySelector('input[name="edit_article_id"]').remove();
        }
        // Unselect all tags
        if (tagsSelect) {
            Array.from(tagsSelect.options).forEach(opt => opt.selected = false);
        }
    });

    // Listen for edit button clicks
    document.querySelectorAll('.edit-article-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            // Set values
            titleInput.value = btn.getAttribute('data-article-title');
            bodyInput.value = btn.getAttribute('data-article-body');
            // Set tags
            if (tagsSelect) {
                let tagIds = btn.getAttribute('data-article-tags').split(',').filter(Boolean);
                Array.from(tagsSelect.options).forEach(opt => {
                    opt.selected = tagIds.includes(opt.value);
                });
            }
            // Add hidden input for edit mode
            let editId = btn.getAttribute('data-article-id');
            let hidden = form.querySelector('input[name="edit_article_id"]');
            if (!hidden) {
                hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = 'edit_article_id';
                form.appendChild(hidden);
            }
            hidden.value = editId;
            // Remove add_article input if present
            let addInput = form.querySelector('input[name="add_article"]');
            if (addInput) addInput.remove();
        });
    });
});
