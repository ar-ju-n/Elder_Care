// notification_ws.js
// Real-time notification WebSocket for chat badge and browser notifications

function createNotificationSocket() {
    const userId = window.CURRENT_USER_ID;
    if (!userId) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const notifySocket = new WebSocket(
        wsScheme + '://' + window.location.host + '/ws/notifications/' + userId + '/'
    );

    notifySocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        // Handle new message notifications
        if (data.event === 'new_message') {
            // Update chat badge
            if (window.updateChatBadge) {
                fetch('/chat/api/unread-count/')
                    .then(res => res.json())
                    .then(data => {
                        window.updateChatBadge(data.unread_count || 0);
                    });
            }

            // Show browser notification if window is not focused
            if (window.notificationSystem && !window.notificationSystem.isWindowVisible()) {
                window.notificationSystem.showNotification(
                    `New message from ${data.sender_name}`,
                    {
                        body: data.message_preview || 'You have a new message',
                        url: data.chat_url,
                        sound: 'message',
                        requireInteraction: false
                    }
                );
            }
        }

        // Handle new chat request notifications
        else if (data.event === 'new_chat_request') {
            // Show browser notification
            if (window.notificationSystem) {
                window.notificationSystem.showNotification(
                    'New Chat Request',
                    {
                        body: `${data.sender_name} wants to chat with you`,
                        url: '/chat/requests/',
                        sound: 'request',
                        requireInteraction: true
                    }
                );
            }
        }

        // Handle request accepted notifications
        else if (data.event === 'request_accepted') {
            // Show browser notification
            if (window.notificationSystem) {
                window.notificationSystem.showNotification(
                    'Chat Request Accepted',
                    {
                        body: `${data.accepter_name} accepted your chat request`,
                        url: data.chat_url,
                        sound: 'default',
                        requireInteraction: false
                    }
                );
            }
        }
    };

    notifySocket.onclose = function () {
        // Try to reconnect after 5 seconds, without reloading the page
        setTimeout(createNotificationSocket, 5000);
    };
}

document.addEventListener('DOMContentLoaded', function () {
    createNotificationSocket();

    // Dropdown logic for notification bell
    const bellDropdown = document.getElementById('notification-bell-dropdown');
    const dropdown = document.getElementById('notification-dropdown');
    if (bellDropdown && dropdown) {
        let loaded = false;
        function loadNotifications() {
            fetch('/forum/notifications/api/recent/')
                .then(resp => resp.json())
                .then(data => {
                    dropdown.innerHTML = '';
                    if (!data.notifications || data.notifications.length === 0) {
                        dropdown.innerHTML = '<div class="text-center text-muted">No notifications</div>';
                    } else {
                        data.notifications.forEach(n => {
                            dropdown.innerHTML += `<a href="${n.url}" class="dropdown-item${n.is_read ? '' : ' fw-bold'}">${n.message}<br><small class="text-muted">${n.created_at}</small></a>`;
                        });
                        dropdown.innerHTML += '<div class="dropdown-divider"></div><a href="/forum/notifications/" class="btn btn-sm btn-outline-secondary w-100 mt-1">View all notifications</a>';
                    }
                });
        }
        bellDropdown.addEventListener('show.bs.dropdown', function () {
            // Mark all as read
            fetch('/forum/notifications/api/mark_read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            }).then(() => {
                // Hide badge immediately
                const badge = document.getElementById('notification-badge');
                if (badge) {
                    badge.style.display = 'none';
                }
            });
            if (!loaded) {
                loadNotifications();
                loaded = true;
            }
        });
        // Optionally reload notifications every time dropdown is shown
        bellDropdown.addEventListener('hide.bs.dropdown', function () {
            loaded = false;
        });
    }

    // Helper to get CSRF token
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
});

