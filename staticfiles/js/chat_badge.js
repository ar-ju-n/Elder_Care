// Handles updating the chat badge in the navbar for new messages
window.updateChatBadge = function updateChatBadge(count) {
  let badge = document.getElementById('chat-badge');
  if (!badge) {
    // Try to find the chat link and add badge if not present
    let chatLink = document.querySelector('.nav-link[data-chat-link]');
    if (chatLink) {
      badge = document.createElement('span');
      badge.id = 'chat-badge';
      badge.className = 'badge bg-danger ms-1';
      chatLink.appendChild(badge);
    }
  }
  if (badge) {
    badge.style.display = count > 0 ? 'inline-block' : 'none';
    badge.textContent = count > 0 ? count : '';
  }
}

// Example polling function (replace with your endpoint)
function pollNewMessages() {
  fetch('/chat/api/unread-count/')
    .then(res => res.json())
    .then(data => {
      updateChatBadge(data.unread_count || 0);
    })
    .catch(() => updateChatBadge(0));
}

// Poll every 1 second
setInterval(pollNewMessages, 1000);
document.addEventListener('DOMContentLoaded', pollNewMessages);
