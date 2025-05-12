// notification_ws.js
// Real-time notification WebSocket for chat badge and browser notifications

function createNotificationSocket() {
    const userId = window.CURRENT_USER_ID;
    if (!userId) return;
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const notifySocket = new WebSocket(
        wsScheme + '://' + window.location.host + '/ws/notifications/' + userId + '/'
    );
    
    notifySocket.onmessage = function(e) {
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
    
    notifySocket.onclose = function() {
        // Try to reconnect after 5 seconds, without reloading the page
        setTimeout(createNotificationSocket, 5000);
    };
}

document.addEventListener('DOMContentLoaded', createNotificationSocket);

