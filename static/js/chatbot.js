document.addEventListener('DOMContentLoaded', function () {
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const chatMessages = document.getElementById('chat-messages');

  chatForm.addEventListener('submit', function (e) {
    console.log('Chat form submitted');
    e.preventDefault();
    const msg = userInput.value.trim();
    if (!msg) return;
    addMessage(msg, 'user');
    userInput.value = '';
    // Send message to backend
    fetch('/chatbot/api/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: 'message=' + encodeURIComponent(msg),
      credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
      if (data.response) {
        addMessage(data.response, 'bot');
      } else if (data.error) {
        addMessage('Error: ' + data.error, 'bot');
      } else {
        addMessage('Unexpected response from server.', 'bot');
      }
    })
    .catch(error => {
      addMessage('Error contacting server. Please try again later.', 'bot');
      console.error(error);
    });
  });

  function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'message user-message' : 'message bot-message';
    // Add avatar icons
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = sender === 'user'
      ? '<i class="bi bi-person-circle" aria-label="You"></i>'
      : '<i class="bi bi-robot" aria-label="AI"></i>';
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    // Improve accessibility with aria-live
    msgDiv.setAttribute('aria-live', 'polite');
  }

  // Typing indicator
  function showTyping() {
    removeTyping();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.innerHTML = '<div class="avatar"><i class="bi bi-robot" aria-label="AI"></i></div><div class="message-content"><span class="dot"></span><span class="dot"></span><span class="dot"></span> <span class="visually-hidden">AI is typing...</span></div>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  function removeTyping() {
    const typing = chatMessages.querySelector('.typing-indicator');
    if (typing) typing.remove();
  }
});
