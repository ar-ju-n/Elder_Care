// tags_ajax.js: AJAX for add, edit, delete tags in content management

document.addEventListener('DOMContentLoaded', function() {
    // CSRF helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Helper: update tag dropdowns
    function updateTagDropdowns(newTag) {
        const tagSelect = document.getElementById('id_tags');
        if (tagSelect) {
            const option = document.createElement('option');
            option.value = newTag.id;
            option.textContent = newTag.name;
            option.selected = true; // Auto-select the new tag
            tagSelect.appendChild(option);
        }
    }

    // Show success message
    function showAlert(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const modalBody = document.querySelector('#tagModal .modal-body');
        if (modalBody) {
            modalBody.insertBefore(alertDiv, modalBody.firstChild);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }, 3000);
        }
    }

    // Add Tag
    const addTagForm = document.getElementById('addTagForm');
    if (addTagForm) {
        addTagForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = this;
            const name = form.tag_name.value.trim();
            if (!name) return;
            
            fetch(form.action, {
                method: 'POST',
                headers: { 
                    'X-CSRFToken': csrftoken, 
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: new URLSearchParams({ tag_name: name })
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    // Add new tag to dropdown
                    updateTagDropdowns(data.tag);
                    
                    // Show success message
                    showAlert(`Tag "${data.tag.name}" ${data.created ? 'created' : 'already exists'} and selected.`);
                    
                    // Clear the form
                    form.tag_name.value = '';
                    
                    // Close modal if Bootstrap is available
                    if (typeof bootstrap !== 'undefined') {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('tagModal'));
                        if (modal) {
                            setTimeout(() => modal.hide(), 1500);
                        }
                    }
                } else {
                    showAlert(data.error || 'An error occurred', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to add tag. Please try again.', 'danger');
            });
        });
    }
});
