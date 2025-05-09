// notification_ws.js
// Real-time notification WebSocket for chat badge

document.addEventListener('DOMContentLoaded', function() {
    const userId = window.CURRENT_USER_ID;
    if (!userId) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const notifySocket = new WebSocket(
        wsScheme + '://' + window.location.host + '/ws/notifications/' + userId + '/'
    );
    notifySocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.event === 'new_message') {
            // Optionally: fetch new unread count from API, or increment badge
            if (window.updateChatBadge) {
                // Option 1: fetch count again for accuracy
                fetch('/chat/api/unread-count/')
                  .then(res => res.json())
                  .then(data => {
                    window.updateChatBadge(data.unread_count || 0);
                  });
                // Option 2: increment badge (if you want instant feedback)
                // window.updateChatBadge((parseInt(document.getElementById('chat-badge').textContent) || 0) + 1);
            }
        }
    };
    notifySocket.onclose = function() {
        // Optionally: try to reconnect
        setTimeout(function() { window.location.reload(); }, 5000);
    };
});
