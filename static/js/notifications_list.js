// notifications_list.js -- Handles marking notifications as read via AJAX with CSRF protection

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

// Example: Mark all notifications as read when clicking a button with id 'markAllReadBtn'
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('markAllReadBtn');
    if (btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            fetch('/accounts/notifications/api/mark_read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({})
            })
            .then(response => {
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(data => {
                // Optionally reload or update UI
                window.location.reload();
            })
            .catch(err => alert('Failed to mark notifications as read.'));
        });
    }
});
