// Handle WebSocket connection for real-time notifications
function setupNotificationWebSocket() {
    if (!window.userData || !window.userData.id) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${window.location.host}/ws/notifications/${window.userData.id}/`;
    
    try {
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log('WebSocket connection established');
        };
        
        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'notification') {
                // Update the notification badge count
                updateNotificationBadge(data.unread_count);
                
                // Show a toast notification if not on the notifications page
                if (window.location.pathname !== '/accounts/notifications/') {
                    showNotificationToast(data.notification);
                }
            }
        };
        
        socket.onclose = function(e) {
            console.log('WebSocket connection closed. Attempting to reconnect...');
            // Attempt to reconnect after 5 seconds
            setTimeout(setupNotificationWebSocket, 5000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        // Store the socket in window for potential reuse
        window.notificationSocket = socket;
    } catch (error) {
        console.error('Error setting up WebSocket:', error);
    }
}

// Update the notification badge in the navbar
function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationsUnreadBadge');
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

// Show a toast notification
function showNotificationToast(notification) {
    // Check if we should show the notification (respect user preferences)
    if (notification && notification.is_silent) return;
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-primary border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('data-bs-delay', '5000');
    
    let actionsHtml = '';
    if (notification.url && notification.url.includes('connection_request')) {
        const requestId = notification.url.split('/').filter(Boolean).pop();
        actionsHtml = `
            <div class="mt-2 pt-2 border-top">
                <a href="/accounts/connections/requests/${requestId}/accept/" class="btn btn-sm btn-success me-2">
                    <i class="bi bi-check-lg"></i> Accept
                </a>
                <a href="/accounts/connections/requests/${requestId}/reject/" class="btn btn-sm btn-outline-light">
                    <i class="bi bi-x-lg"></i> Reject
                </a>
            </div>`;
    }
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <div class="d-flex justify-content-between align-items-center">
                    <strong class="me-auto">${notification.title || 'New Notification'}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="mt-1">${notification.message || ''}</div>
                ${actionsHtml}
            </div>
        </div>`;
    
    // Add to toast container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1100';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove the toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
    
    // Handle click on the toast body
    if (notification.url && !notification.url.includes('connection_request')) {
        toast.querySelector('.toast-body').addEventListener('click', function() {
            window.location.href = notification.url;
        });
    }
}

// Initialize notification system when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up WebSocket connection
    setupNotificationWebSocket();
    
    // Mark notification as read when clicked in the dropdown
    document.addEventListener('click', function(e) {
        const notificationLink = e.target.closest('.notification-link');
        if (!notificationLink) return;
        
        const notificationId = notificationLink.dataset.notificationId;
        if (!notificationId) return;
        
        // Mark as read in the backend
        fetch('/accounts/notifications/api/mark_read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                notification_id: notificationId
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error('Failed to mark notification as read');
            }
            // Update the UI
            const notificationItem = notificationLink.closest('.dropdown-item');
            if (notificationItem) {
                notificationItem.classList.remove('unread');
                const badge = notificationItem.querySelector('.badge');
                if (badge) badge.remove();
                
                // Update the unread count
                updateUnreadCount(-1);
            }
        }).catch(error => {
            console.error('Error marking notification as read:', error);
        });
    });
});

// Helper function to get CSRF token from cookies
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

// Helper function to update the unread count in the navbar
function updateUnreadCount(change) {
    const badge = document.getElementById('notificationsUnreadBadge');
    if (!badge) return;
    
    let currentCount = parseInt(badge.textContent) || 0;
    currentCount += change;
    
    if (currentCount <= 0) {
        badge.style.display = 'none';
    } else {
        badge.textContent = currentCount > 99 ? '99+' : currentCount;
        badge.style.display = 'inline-block';
    }
}
