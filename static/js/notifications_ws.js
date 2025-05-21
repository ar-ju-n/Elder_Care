// notifications_ws.js
// Handles real-time notifications via Django Channels WebSocket

(function() {
    // Only run if user is authenticated and the notification bell exists
    const bell = document.getElementById('notificationDropdown');
    if (!bell || !window.isAuthenticated || !window.userId) return;

    // Build WebSocket URL
    let ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    let ws_path = `${ws_scheme}://${window.location.host}/ws/notifications/`;
    const socket = new WebSocket(ws_path);

    socket.onopen = function() {
        // Optionally log connection
        // console.log('WebSocket for notifications connected');
    };
    socket.onclose = function(e) {
        // Optionally log disconnect
        // console.log('WebSocket for notifications closed');
    };
    socket.onerror = function(e) {
        // Optionally log errors
        // console.error('WebSocket error:', e);
    };

    socket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            // You may want to customize this based on your backend event format
            if (data.message || data.msg || data.notification) {
                // New notification received, refresh the notification dropdown
                if (typeof fetchNotifications === 'function') {
                    fetchNotifications();
                } else if (window.fetchNotifications) {
                    window.fetchNotifications();
                }
                // Optionally show a toast or highlight
            }
        } catch (err) {
            // Ignore parse errors
        }
    };

    // Expose for debugging
    window.NotificationsSocket = socket;
})();
