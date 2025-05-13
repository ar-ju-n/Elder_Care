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
    msgDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});
