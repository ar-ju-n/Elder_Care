// Real-time chat using WebSocket for chat_room.html

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-messages');
    const messageInput = document.querySelector('input[name="message"]');
    const chatForm = document.getElementById('chat-form');
    const typingIndicator = document.getElementById('typing-indicator');
    const userName = window.CURRENT_USER_USERNAME || '';
    const requestId = window.CHAT_REQUEST_ID;
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsPath = `${wsScheme}://${window.location.host}/ws/chat/${requestId}/`;
    const socket = new WebSocket(wsPath);
    let typingTimeout = null;
    let lastTyped = 0;

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'chat_message') {
            const li = document.createElement('li');
            li.className = 'mb-2';
            if (data.username === userName) {
                li.classList.add('text-end');
            }
            li.innerHTML = `<span class="fw-bold">${data.username}:</span> ${data.message}`;
            chatBox.appendChild(li);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else if (data.type === 'typing') {
            if (data.username !== userName) {
                typingIndicator.style.display = 'block';
                if (typingTimeout) clearTimeout(typingTimeout);
                typingTimeout = setTimeout(() => {
                    typingIndicator.style.display = 'none';
                }, 1500);
            }
        }
    };

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            socket.send(JSON.stringify({ 'message': message }));
            messageInput.value = '';
        }
    });

    messageInput.addEventListener('input', function() {
        // Send typing event if user hasn't typed in the last 900ms
        const now = Date.now();
        if (now - lastTyped > 900) {
            socket.send(JSON.stringify({ 'type': 'typing' }));
            lastTyped = now;
        }
    });
});
