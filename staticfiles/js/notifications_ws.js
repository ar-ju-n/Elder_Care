// notifications_ws.js
// Handles real-time notifications via Django Channels WebSocket

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated and user data is available
    if (!window.userData || !window.userData.isAuthenticated) {
        console.log('User not authenticated or user data not available');
        return;
    }
    
    const notificationBell = document.getElementById('notificationDropdown');
    if (!notificationBell) return;

    // Helper function to get CSRF token
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

    // Update notification badge
    function updateBadge(count) {
        const badge = document.getElementById('notificationsUnreadBadge');
        if (!badge) return;
        
        if (count > 0) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }

    // Mark all notifications as read
    function markAllAsRead() {
        fetch('/accounts/notifications/api/mark_read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateBadge(0);
                // Update all notification items to appear as read
                document.querySelectorAll('#notificationsListContainer .dropdown-item').forEach(item => {
                    item.classList.remove('fw-bold');
                });
            }
        });
    }


    // Initialize WebSocket connection
    let socket = null;
    
    function connectWebSocket() {
        if (!window.userData || !window.userData.userId) {
            console.error('No user ID available for WebSocket connection');
            return;
        }
        
        const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const ws_path = `${ws_scheme}://${window.location.host}/ws/notifications/${window.userData.userId}/`;
        
        console.log('Connecting to WebSocket at:', ws_path);
        socket = new WebSocket(ws_path);

        socket.onopen = function() {
            console.log('WebSocket connection established');
            // Fetch notifications immediately after connection
            fetchNotifications();
        };

        socket.onclose = function(e) {
            console.log('WebSocket connection closed:', e.code, e.reason);
            console.log('Attempting to reconnect in 5 seconds...');
            // Attempt to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };

        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            // Close the socket to trigger reconnection
            if (socket) {
                socket.close();
            }
        };

        socket.onmessage = function(e) {
            console.log('WebSocket message received:', e.data);
            try {
                const data = JSON.parse(e.data);
                console.log('Parsed message data:', data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
    }
    
    function handleWebSocketMessage(data) {
        if (!data || !data.type) {
            console.error('Invalid WebSocket message format:', data);
            return;
        }

        switch(data.type) {
            case 'new_notification':
                handleNewNotification(data);
                break;
            case 'unread_count':
                updateBadge(data.count || 0);
                break;
            default:
                console.log('Unhandled WebSocket message type:', data.type);
        }
    }
    
    function handleNewNotification(notification) {
        console.log('New notification received:', notification);
        
        // Play notification sound if available
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
        } catch (e) {
            console.log('Notification sound error:', e);
        }
        
        // Update badge
        if (notification.unread_count !== undefined) {
            updateBadge(notification.unread_count);
        }
        
        // Show desktop notification if permission is granted
        if (Notification.permission === 'granted' && notification.title) {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/logo.png'
            });
        }
        
        // Refresh notifications list if dropdown is open
        const dropdown = document.getElementById('notificationsDropdownMenu');
        if (dropdown && dropdown.classList.contains('show')) {
            fetchNotifications();
        }
    }
    
    // Function to fetch notifications
    function fetchNotifications() {
        fetch('/accounts/notifications/api/recent/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch notifications');
                }
                return response.json();
            })
            .then(data => {
                const container = document.getElementById('notificationsListContainer');
                if (!container) return;
                
                let html = '';
                let unreadCount = 0;
                
                if (data.notifications && data.notifications.length > 0) {
                    data.notifications.forEach(notification => {
                        if (!notification.is_read) unreadCount++;
                        html += `
                            <a href="${notification.url || '#'}" class="dropdown-item ${notification.is_read ? '' : 'fw-bold'}">
                                <div class="d-flex align-items-center">
                                    <div class="flex-grow-1">
                                        <div class="small">${notification.message}</div>
                                        <span class="text-muted small">${notification.timestamp}</span>
                                    </div>
                                </div>
                            </a>
                            <div class="dropdown-divider"></div>
                        `;
                    });
                } else {
                    html = '<div class="text-center p-3 text-muted">No notifications</div>';
                }
                
                container.innerHTML = html;
                updateBadge(unreadCount);
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
            });
    }
    
    // Initial connection
    connectWebSocket();

    // Request notification permission on page load
    if ('Notification' in window) {
        if (Notification.permission !== 'denied' && Notification.permission !== 'granted') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission:', permission);
            });
        }
    }

    // Mark all as read when clicking the button
    const markAllButton = document.getElementById('markAllNotificationsRead');
    if (markAllButton) {
        markAllButton.addEventListener('click', function(e) {
            e.preventDefault();
            markAllAsRead();
        });
    }

    // Initialize notification count on page load
    fetch('/accounts/notifications/api/recent/')
        .then(response => response.json())
        .then(data => {
            if (data.notifications) {
                updateBadge(data.notifications.filter(n => !n.is_read).length);
            }
        });

    // Expose functions for other scripts
    window.markAllNotificationsRead = markAllAsRead;
    window.updateNotificationBadge = updateBadge;
});
