document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = userInput.value.trim();
            if (!message) return;

            // Add user message to chat window
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'message user-message animate__animated animate__fadeInRight';
            userMsgDiv.innerHTML = `<div class="message-content">${message}</div>`;
            chatMessages.appendChild(userMsgDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Clear input
            userInput.value = '';
            userInput.focus();

            // Send message to backend (assume /chatbot/ endpoint, POST)
            const formData = new FormData();
            formData.append('message', message);
            fetch('/chatbot/api/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Add bot response to chat window
                const botMsgDiv = document.createElement('div');
                botMsgDiv.className = 'message bot-message animate__animated animate__fadeInLeft';
                botMsgDiv.innerHTML = `<div class="message-content">${data.response || data.reply || 'Sorry, no response.'}</div>`;
                chatMessages.appendChild(botMsgDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(() => {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message bot-message animate__animated animate__fadeInLeft';
                errorDiv.innerHTML = `<div class="message-content text-danger">Error communicating with server.</div>`;
                chatMessages.appendChild(errorDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        });
    }

    // Helper to get CSRF token from cookie
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
});
