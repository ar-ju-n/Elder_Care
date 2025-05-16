// Polls the server every 30 seconds for the user's unread notification count and updates the navbar badge.
(function () {
    function updateForumNotificationBadge() {
        fetch('/forum/api/unread_notifications_count/', {
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById('notification-badge');
                if (badge) {
                    if (data.unread_count > 0) {
                        badge.textContent = data.unread_count;
                        badge.style.display = '';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            });
    }
    document.addEventListener('DOMContentLoaded', function () {
        updateForumNotificationBadge();
        setInterval(updateForumNotificationBadge, 30000); // 30 seconds
    });
})();
