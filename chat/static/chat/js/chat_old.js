// Chat Application Main Module
class ChatApp {
    constructor() {
        // DOM Elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.attachmentInput = document.getElementById('attachmentInput');
        this.attachmentPreview = document.getElementById('attachmentPreview');
        this.imagePreview = document.getElementById('imagePreview');
        this.filePreview = document.getElementById('filePreview');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.removeAttachmentBtn = document.getElementById('removeAttachment');
        this.sendButton = document.getElementById('sendButton');
        this.loadMoreBtn = document.getElementById('loadMoreBtn');
        this.loadingMessages = document.getElementById('loadingMessages');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // State
        this.chatRequestId = this.messageForm ? this.messageForm.querySelector('input[name="chat_request_id"]').value : null;
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.isTyping = false;
        this.lastTypingTime = 0;
        this.typingTimer = null;
        this.socket = null;
        this.TYPING_TIMER_LENGTH = 1000; // 1 second after no typing
        
        // Initialize the app
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadMessages();
        
        // Initialize message input auto-resize and validation
        if (this.messageInput) {
            this.messageInput.addEventListener('input', () => {
                this.messageInput.style.height = 'auto';
                this.messageInput.style.height = (this.messageInput.scrollHeight) + 'px';
                this.validateMessageInput();
                this.updateTyping();
            });
        }
    }
}
// Setup event listeners
function setupEventListeners() {
    const messageInput = document.getElementById('messageInput');
    const attachmentInput = document.getElementById('attachmentInput');
    const messageForm = document.getElementById('messageForm');
    
    if (messageInput) {
        messageInput.addEventListener('focus', () => {
            document.addEventListener('keydown', handleKeyDown);
        });
        
        messageInput.addEventListener('blur', () => {
            document.removeEventListener('keydown', handleKeyDown);
            stopTyping();
        });
        
        // Typing indicator is now handled here
        messageInput.addEventListener('input', function() {
            updateTyping();
        });
    }
    
    if (attachmentInput) {
        attachmentInput.addEventListener('change', handleFileSelection);
    }
    
    if (messageForm) {
        messageForm.addEventListener('submit', handleMessageSubmit);
    }
}

// Handle keyboard shortcuts
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const sendButton = document.getElementById('sendButton');
        if (sendButton && !sendButton.disabled) {
            sendButton.click();
        }
    }
}

// Validate message input
function validateMessageInput() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    if (!messageInput || !sendButton) return;
    
    const hasText = messageInput.value.trim().length > 0;
    const hasAttachment = document.getElementById('attachmentPreview')?.classList.contains('d-none') === false;
    
    sendButton.disabled = !(hasText || hasAttachment);
}

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const attachmentInput = document.getElementById('attachmentInput');
const attachmentPreview = document.getElementById('attachmentPreview');
const imagePreview = document.getElementById('imagePreview');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeAttachmentBtn = document.getElementById('removeAttachment');
const sendButton = document.getElementById('sendButton');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const loadingMessages = document.getElementById('loadingMessages');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');
const chatRequestId = messageForm ? messageForm.querySelector('input[name="chat_request_id"]').value : null;
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let isTyping = false;
let lastTypingTime;
let typingTimer;
let socket;
const TYPING_TIMER_LENGTH = 1000; // 1 second after no typing

// Show message status
function showMessageStatus(status) {
    const statusElement = document.getElementById('messageStatus');
    if (!statusElement) return;
    
    const icon = statusElement.querySelector('.status-icon');
    const text = statusElement.querySelector('.status-text');
    
    if (!icon || !text) return;
    
    switch (status) {
        case 'sending':
            icon.innerHTML = '<i class="bi bi-arrow-up-circle"></i>';
            text.textContent = 'Sending...';
            break;
        case 'sent':
            icon.innerHTML = '<i class="bi bi-check2"></i>';
            text.textContent = 'Sent';
            break;
        case 'delivered':
            icon.innerHTML = '<i class="bi bi-check2-all"></i>';
            text.textContent = 'Delivered';
            break;
        case 'read':
            icon.innerHTML = '<i class="bi bi-check2-all text-primary"></i>';
            text.textContent = 'Read';
            break;
        case 'error':
            icon.innerHTML = '<i class="bi bi-exclamation-circle text-danger"></i>';
            text.textContent = 'Failed to send';
            break;
    }
    
    statusElement.classList.remove('d-none');
    statusElement.classList.add('visible');
    
    // Hide after delay
    if (['sent', 'delivered', 'read'].includes(status)) {
        setTimeout(() => {
            statusElement.classList.remove('visible');
            setTimeout(() => {
                statusElement.classList.add('d-none');
            }, 300);
        }, 3000);
    }
}

// Initialize WebSocket connection
function connectWebSocket() {
    const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsPath = wsScheme + window.location.host + '/ws/chat/' + chatRequestId + '/';
    
    socket = new WebSocket(wsPath);
    
    socket.onopen = function(e) {
        console.log('WebSocket connection established');
        // Load initial messages
        loadMessages();
    };
    
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Message received:', data);
        
        if (data.type === 'chat_message') {
            // Add new message to the chat
            addMessageToChat(data.message, false);
            // Mark as read
            markMessageAsRead(data.message.id);
            // Scroll to bottom
            scrollToBottom();
        } 
        else if (data.type === 'typing') {
            // Show typing indicator
            if (data.user_id !== '{{ request.user.id }}') {
                showTypingIndicator();
            }
        }
        else if (data.type === 'stop_typing') {
            // Hide typing indicator
            hideTypingIndicator();
        }
        else if (data.type === 'message_read') {
            // Update message read status
            updateMessageReadStatus(data.message_id, data.read_by);
        }
    };
    
    socket.onclose = function(e) {
        console.log('WebSocket connection closed. Attempting to reconnect...');
        // Try to reconnect after 5 seconds
        setTimeout(initWebSocket, 5000);
    };
    
    socket.onerror = function(err) {
        console.error('WebSocket error:', err);
    };
}

// Load messages with pagination
async function loadMessages() {
    if (isLoading || !hasMore) return;
    
    isLoading = true;
    
    try {
        const response = await fetch(`/chat/room/${chatRequestId}/load-more/?page=${currentPage}`);
        const data = await response.json();
        
        if (data.messages && data.messages.length > 0) {
            // If it's the first page, clear the loading indicator
            if (currentPage === 1) {
                loadingMessages.style.display = 'none';
            }
            
            // Add messages to the top of the container
            const fragment = document.createDocumentFragment();
            
            data.messages.reverse().forEach(msg => {
                const messageElement = createMessageElement(msg);
                fragment.prepend(messageElement);
            });
            
            messagesContainer.prepend(fragment);
            
            // Show/hide load more button
            hasMore = data.has_more;
            if (hasMore) {
                loadMoreBtn.style.display = 'block';
            } else {
                loadMoreBtn.style.display = 'none';
            }
            
            // If it's the first page, scroll to bottom
            if (currentPage === 1) {
                scrollToBottom();
            } else {
                // Maintain scroll position when loading older messages
                const firstMessage = messagesContainer.firstElementChild;
                const scrollHeightBefore = firstMessage ? firstMessage.offsetTop : 0;
                
                // After adding messages, adjust scroll position
                setTimeout(() => {
                    if (firstMessage) {
                        const scrollHeightAfter = firstMessage.offsetTop;
                        window.scrollTo(0, window.scrollY + (scrollHeightAfter - scrollHeightBefore));
                    }
                }, 0);
            }
            
            currentPage++;
        } else if (currentPage === 1) {
            // No messages at all
            loadingMessages.style.display = 'none';
            messagesContainer.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="bi bi-chat-square-text d-block mb-2" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    <p class="mb-0">No messages yet. Start the conversation!</p>
                </div>
            `;
            loadMoreBtn.style.display = 'none';
        } else {
            // No more messages to load
            hasMore = false;
            loadMoreBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        loadingMessages.innerHTML = `
            <div class="alert alert-danger">
                Error loading messages. <button class="btn btn-sm btn-outline-danger" onclick="window.location.reload()">Retry</button>
            </div>
        `;
    } finally {
        isLoading = false;
    }
}

// Create message element from message data
function createMessageElement(message) {
    const isCurrentUser = message.sender.id === '{{ request.user.id }}';
    const messageTime = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let messageContent = '';
    
    // Handle attachment if present
    if (message.attachment) {
        const fileExtension = message.attachment_name ? message.attachment_name.split('.').pop().toLowerCase() : '';
        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension);
        
        if (isImage) {
            messageContent += `
                <div class="message-attachment mb-2">
                    <img src="${message.attachment}" alt="Attachment" class="img-fluid rounded" loading="lazy">
                </div>
            `;
        } else {
            messageContent += `
                <div class="message-attachment mb-2">
                    <div class="file-attachment p-3 bg-light rounded">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-file-earmark-text fs-1 me-3"></i>
                            <div class="flex-grow-1">
                                <div class="fw-semibold text-truncate">${message.attachment_name || 'File'}</div>
                                <small class="text-muted">${message.file_size || ''}</small>
                            </div>
                            <a href="${message.attachment}" class="btn btn-sm btn-outline-primary ms-2" download>
                                <i class="bi bi-download"></i>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    // Add message text if present
    if (message.message) {
        messageContent += `
            <div class="message-text">
                ${message.message.replace(/\n/g, '<br>')}
            </div>
        `;
    }
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `message-wrapper ${isCurrentUser ? 'sent' : 'received'}`;
    messageElement.dataset.messageId = message.id;
    messageElement.innerHTML = `
        <div class="message ${isCurrentUser ? 'sent' : 'received'}">
            ${messageContent}
            <div class="message-time">
                ${messageTime}
                ${isCurrentUser ? `
                    <span class="message-status ${message.is_read ? 'read' : ''}">
                        <i class="bi bi-${message.is_read ? 'check2-all' : 'check2'}"></i>
                    </span>
                ` : ''}
            </div>
        </div>
    `;
    
    return messageElement;
}

// Add a new message to the chat
function addMessageToChat(messageData, isCurrentUser = true) {
    // If it's the first message, clear the "no messages" placeholder
    if (messagesContainer.querySelector('.text-muted')) {
        messagesContainer.innerHTML = '';
    }
    
    const messageElement = createMessageElement({
        ...messageData,
        sender: {
            id: isCurrentUser ? '{{ request.user.id }}' : messageData.sender_id,
            name: isCurrentUser ? 'You' : '{{ other_user.get_full_name|default:other_user.username }}',
            avatar: isCurrentUser ? '{{ request.user.profile_picture.url|default:"/static/images/default-avatar.png" }}' : '{{ other_user.profile_picture.url|default:"/static/images/default-avatar.png" }}'
        }
    });
    
    messagesContainer.appendChild(messageElement);
    return messageElement;
}

// Mark a message as read
function markMessageAsRead(messageId) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            'type': 'read_receipt',
            'message_id': messageId
        }));
    }
}

// Update message read status
function updateMessageReadStatus(messageId, readBy) {
    const messageElement = messagesContainer.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        const statusElement = messageElement.querySelector('.message-status');
        if (statusElement) {
            statusElement.innerHTML = '<i class="bi bi-check2-all"></i>';
            statusElement.classList.add('read');
        }
    }
}

// Show typing indicator
function showTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.classList.remove('d-none');
        setTimeout(() => {
            typingIndicator.classList.add('visible');
        }, 10);
    }
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.classList.remove('visible');
        setTimeout(() => {
            typingIndicator.classList.add('d-none');
        }, 300);
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle form submission
async function handleMessageSubmit(e) {
    e.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const attachmentInput = document.getElementById('attachmentInput');
    const sendButton = document.getElementById('sendButton');
    const sendButtonIcon = document.getElementById('sendButtonIcon');
    const sendingSpinner = document.getElementById('sendingSpinner');
    
    if (!messageInput || !sendButton) return;
    
    const messageText = messageInput.value.trim();
    const attachmentFile = attachmentInput?.files[0];
    
    // Don't send empty messages
    if (!messageText && !attachmentFile) return;
    
    // Disable form while sending
    sendButton.disabled = true;
    if (sendButtonIcon) sendButtonIcon.classList.add('d-none');
    if (sendingSpinner) sendingSpinner.classList.remove('d-none');
    
    try {
        // Show sending status
        showMessageStatus('sending');
        
        // Create FormData for the request
        const formData = new FormData();
        formData.append('message', messageText);
        formData.append('chat_request_id', chatRequestId);
        
        if (attachmentFile) {
            formData.append('attachment', attachmentFile);
            
            // Show file info
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
        }
        
        // Enable send button if message input is empty
        if (messageInput.value.trim() === '') {
            sendButton.disabled = false;
        }
    }
    
    // Reset attachment preview
    function resetAttachmentPreview() {
        attachmentPreview.classList.add('d-none');
        imagePreview.classList.add('d-none');
        filePreview.classList.add('d-none');
        imagePreview.src = '#';
        fileName.textContent = '';
        fileSize.textContent = '';
        attachmentInput.value = '';
        
        // Disable send button if message input is also empty
        if (messageInput.value.trim() === '') {
            sendButton.disabled = true;
        }
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Typing indicator
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            updateTyping();
        });
    }
    
    // Update typing status
    function updateTyping() {
        if (!isTyping) {
            isTyping = true;
            socket?.send(JSON.stringify({
                'type': 'typing',
                'is_typing': true
            }));
        }
        
        lastTypingTime = new Date().getTime();
        
        if (typingTimer) {
            clearTimeout(typingTimer);
        }
        
        typingTimer = setTimeout(stopTyping, TYPING_TIMER_LENGTH);
    }
    
    // Stop typing
    function stopTyping() {
        const timer = new Date().getTime();
        const timeDiff = timer - (lastTypingTime || 0);
        
        if (isTyping && timeDiff >= TYPING_TIMER_LENGTH) {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    'type': 'typing',
                    'is_typing': false,
                    'user_id': '{{ request.user.id }}'
                }));
            }
            isTyping = false;
        }
    }
    
    // Load more messages when scrolling to top
    if (messagesContainer) {
        messagesContainer.addEventListener('scroll', function() {
            if (messagesContainer.scrollTop === 0 && hasMore && !isLoading) {
                loadMessages();
            }
        });
    }
    
    // Load more button click
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function(e) {
            e.preventDefault();
            loadMessages();
        });
    }
    
    // Initialize chat
    if (chatRequestId) {
        initWebSocket();
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        // Adjust chat container height
        const headerHeight = document.querySelector('.chat-room-header').offsetHeight;
        const inputHeight = document.querySelector('.chat-input-container').offsetHeight;
        const typingHeight = typingIndicator.offsetHeight;
        const windowHeight = window.innerHeight;
        
        chatMessages.style.height = (windowHeight - headerHeight - inputHeight - typingHeight - 20) + 'px';
    });
    
    // Trigger initial resize
    window.dispatchEvent(new Event('resize'));
    
    // Focus the message input when the page loads
    if (messageInput) {
        messageInput.focus();
    }
    
    // Handle delete chat confirmation
    const deleteChatModal = document.getElementById('deleteChatModal');
    if (deleteChatModal) {
        const confirmDeleteBtn = document.getElementById('confirmDeleteChat');
        
        confirmDeleteBtn.addEventListener('click', function() {
            // Show loading state
            const originalText = confirmDeleteBtn.innerHTML;
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
            
            // In a real app, you would make an AJAX request to delete the chat
            // For now, we'll just simulate it with a timeout
            setTimeout(() => {
                // Close the modal
                const modal = bootstrap.Modal.getInstance(deleteChatModal);
                modal.hide();
                
                // Show success message
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success';
                successAlert.textContent = 'Chat deleted successfully';
                document.querySelector('.container').prepend(successAlert);
                
                // Redirect to chat list after a delay
                setTimeout(() => {
                    window.location.href = '{% url "chat:chat_list" %}';
                }, 1500);
                
                // Reset button state (in case the modal is closed before redirect)
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.innerHTML = originalText;
            }, 1000);
        });
    }
});
