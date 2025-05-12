// JavaScript for real-time notifications (moved from base.html)
document.addEventListener('DOMContentLoaded', function() {
    if (window.userIsAuthenticated) {
        const userId = window.userId;
        const toastEl = document.getElementById('notification-toast');
        const toastBody = document.getElementById('notification-toast-body');
        let toastInstance;
        if (window.bootstrap && window.bootstrap.Toast) {
            toastInstance = new bootstrap.Toast(toastEl);
        }
        // Connect to notifications WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/ws/notifications/${userId}/`;
        const socket = new WebSocket(wsUrl);
        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.event === 'new_message') {
                // Show toast popup
                const preview = data.message_preview || 'You have a new message!';
                const sender = data.sender_name || 'Someone';
                toastBody.innerHTML = `<strong>${sender}</strong>: ${preview} <a href="${data.chat_url}" class="ms-2 btn btn-sm btn-light">Open Chat</a>`;
                if (toastInstance) toastInstance.show();
                // Update unread badge in accepted elders list if present
                if (data.chat_url && data.chat_url.includes('/chat/room/')) {
                    const reqId = data.chat_url.split('/').filter(Boolean).pop();
                    const badge = document.querySelector(`[data-chat-request="${reqId}"] .badge`);
                    if (badge) {
                        let count = parseInt(badge.textContent) || 0;
                        badge.textContent = (count + 1) + ' new';
                        badge.classList.remove('d-none');
                    }
                }
            }
            if (data.event === 'request_accepted') {
                toastBody.innerHTML = `<strong>${data.accepter_name}</strong> accepted your chat request. <a href="${data.chat_url}" class="ms-2 btn btn-sm btn-light">Open Chat</a>`;
                if (toastInstance) toastInstance.show();
            }
        };
        socket.onclose = function() {
            // Optionally, try to reconnect
        };
    }
});
