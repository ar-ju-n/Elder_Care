/**
 * Chat Application
 * Handles real-time messaging, file uploads, and typing indicators
 */

class ChatApp {
    constructor() {
        // Bind methods
        this.init = this.init.bind(this);
        this.setupEventListeners = this.setupEventListeners.bind(this);
        this.handleMessageSubmit = this.handleMessageSubmit.bind(this);
        this.handleFileSelection = this.handleFileSelection.bind(this);
        this.resetAttachmentPreview = this.resetAttachmentPreview.bind(this);
        this.showAttachmentPreview = this.showAttachmentPreview.bind(this);
        this.formatFileSize = this.formatFileSize.bind(this);
        this.updateTyping = this.updateTyping.bind(this);
        this.stopTyping = this.stopTyping.bind(this);
        this.connectWebSocket = this.connectWebSocket.bind(this);
        this.loadMessages = this.loadMessages.bind(this);
        this.createMessageElement = this.createMessageElement.bind(this);
        this.addMessageToChat = this.addMessageToChat.bind(this);
        this.markMessageAsRead = this.markMessageAsRead.bind(this);
        this.updateMessageReadStatus = this.updateMessageReadStatus.bind(this);
        this.showTypingIndicator = this.showTypingIndicator.bind(this);
        this.hideTypingIndicator = this.hideTypingIndicator.bind(this);
        this.scrollToBottom = this.scrollToBottom.bind(this);
        this.showMessageStatus = this.showMessageStatus.bind(this);
        this.validateMessageInput = this.validateMessageInput.bind(this);
        this.handleKeyDown = this.handleKeyDown.bind(this);

        // Initialize the app when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this.init);
        } else {
            this.init();
        }
    }

    // Initialize the chat application
    init() {
        // Get DOM elements
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
        this.messageStatus = document.getElementById('messageStatus');
        this.sendButtonIcon = document.getElementById('sendButtonIcon');
        this.sendingSpinner = document.getElementById('sendingSpinner');
        
        // Get chat request ID from the form
        this.chatRequestId = this.messageForm ? 
            (this.messageForm.querySelector('input[name="chat_request_id"]')?.value || null) : null;
        
        // Initialize state
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.isTyping = false;
        this.lastTypingTime = 0;
        this.typingTimer = null;
        this.socket = null;
        this.TYPING_TIMER_LENGTH = 1000; // 1 second after no typing
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Connect to WebSocket
        if (this.chatRequestId) {
            this.connectWebSocket();
        }
        
        // Load initial messages
        this.loadMessages();
        
        // Initialize message input auto-resize and validation
        if (this.messageInput) {
            this.messageInput.addEventListener('input', () => {
                this.messageInput.style.height = 'auto';
                this.messageInput.style.height = (this.messageInput.scrollHeight) + 'px';
                this.validateMessageInput();
                this.updateTyping();
            });
            
            // Initial validation
            this.validateMessageInput();
        }
    }
    
    // Set up all event listeners
    setupEventListeners() {
        // Message input events
        if (this.messageInput) {
            this.messageInput.addEventListener('focus', () => {
                document.addEventListener('keydown', this.handleKeyDown);
            });
            
            this.messageInput.addEventListener('blur', () => {
                document.removeEventListener('keydown', this.handleKeyDown);
                this.stopTyping();
            });
        }
        
        // Attachment handling
        if (this.attachmentInput) {
            this.attachmentInput.addEventListener('change', this.handleFileSelection);
        }
        
        if (this.removeAttachmentBtn) {
            this.removeAttachmentBtn.addEventListener('click', this.resetAttachmentPreview);
        }
        
        // Form submission
        if (this.messageForm) {
            this.messageForm.addEventListener('submit', this.handleMessageSubmit);
        }
        
        // Load more messages
        if (this.loadMoreBtn) {
            this.loadMoreBtn.addEventListener('click', this.loadMessages);
        }
        
        // Infinite scroll
        if (this.messagesContainer) {
            this.messagesContainer.addEventListener('scroll', () => {
                if (this.messagesContainer.scrollTop === 0 && !this.isLoading && this.hasMore) {
                    this.loadMessages();
                }
            });
        }
    }
    
    // Handle keyboard shortcuts
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.sendButton && !this.sendButton.disabled) {
                this.sendButton.click();
            }
        }
    }
    
    // Validate message input and update send button state
    validateMessageInput() {
        if (!this.messageInput || !this.sendButton) return;
        
        const hasText = this.messageInput.value.trim().length > 0;
        const hasAttachment = this.attachmentInput?.files.length > 0;
        
        this.sendButton.disabled = !(hasText || hasAttachment);
    }
    
    // Show message status (sent, delivered, read, error)
    showMessageStatus(status) {
        if (!this.messageStatus) return;
        
        const icon = this.messageStatus.querySelector('.status-icon');
        const text = this.messageStatus.querySelector('.status-text');
        
        if (!icon || !text) return;
        
        // Update status based on type
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
        
        // Show status
        this.messageStatus.classList.remove('d-none');
        this.messageStatus.classList.add('visible');
        
        // Auto-hide after delay for non-error statuses
        if (['sent', 'delivered', 'read'].includes(status)) {
            setTimeout(() => {
                this.messageStatus.classList.remove('visible');
                setTimeout(() => {
                    this.messageStatus.classList.add('d-none');
                }, 300);
            }, 3000);
        }
    }
    
    // Handle file selection for attachments
    handleFileSelection(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        this.showAttachmentPreview(file);
        this.validateMessageInput();
    }
    
    // Show preview for the selected file
    showAttachmentPreview(file) {
        if (!file || !this.attachmentPreview) return;
        
        this.attachmentPreview.classList.remove('d-none');
        
        // Check if it's an image
        if (file.type.match('image.*')) {
            // Show image preview
            if (this.imagePreview) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.imagePreview.src = e.target.result;
                    this.imagePreview.classList.remove('d-none');
                    if (this.filePreview) this.filePreview.classList.add('d-none');
                };
                reader.readAsDataURL(file);
            }
        } else {
            // Show file info for non-image files
            if (this.filePreview) {
                this.filePreview.classList.remove('d-none');
                if (this.imagePreview) this.imagePreview.classList.add('d-none');
                
                if (this.fileName) {
                    this.fileName.textContent = file.name;
                }
                
                if (this.fileSize) {
                    this.fileSize.textContent = this.formatFileSize(file.size);
                }
            }
        }
    }
    
    // Reset attachment preview
    resetAttachmentPreview() {
        if (this.attachmentPreview) {
            this.attachmentPreview.classList.add('d-none');
        }
        
        if (this.imagePreview) {
            this.imagePreview.src = '#';
            this.imagePreview.classList.add('d-none');
        }
        
        if (this.filePreview) {
            this.filePreview.classList.add('d-none');
        }
        
        if (this.attachmentInput) {
            this.attachmentInput.value = '';
        }
        
        this.validateMessageInput();
    }
    
    // Format file size in human-readable format
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Update typing status
    updateTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    'type': 'typing',
                    'is_typing': true,
                    'user_id': this.userId || 'current_user'
                }));
            }
        }
        
        this.lastTypingTime = new Date().getTime();
        
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        this.typingTimer = setTimeout(this.stopTyping, this.TYPING_TIMER_LENGTH);
    }
    
    // Stop typing indicator
    stopTyping() {
        const timer = new Date().getTime();
        const timeDiff = timer - (this.lastTypingTime || 0);
        
        if (this.isTyping && timeDiff >= this.TYPING_TIMER_LENGTH) {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    'type': 'typing',
                    'is_typing': false,
                    'user_id': this.userId || 'current_user'
                }));
            }
            this.isTyping = false;
        }
    }
    
    // Show typing indicator for other users
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('d-none');
            setTimeout(() => {
                this.typingIndicator.classList.add('visible');
            }, 10);
            
            this.scrollToBottom();
        }
    }
    
    // Hide typing indicator
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('visible');
            setTimeout(() => {
                this.typingIndicator.classList.add('d-none');
            }, 300);
        }
    }
    
    // Scroll to the bottom of the chat
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }
    
    // Connect to WebSocket for real-time updates
    connectWebSocket() {
        if (!this.chatRequestId) return;
        
        const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsPath = wsScheme + window.location.host + '/ws/chat/' + this.chatRequestId + '/';
        
        this.socket = new WebSocket(wsPath);
        
        this.socket.onopen = () => {
            console.log('WebSocket connection established');
        };
        
        this.socket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                console.log('WebSocket message received:', data);
                
                switch (data.type) {
                    case 'chat_message':
                        this.addMessageToChat(data.message, data.message.sender_id === this.userId);
                        this.scrollToBottom();
                        
                        // Mark as read if it's our message
                        if (data.message.sender_id !== this.userId) {
                            this.markMessageAsRead(data.message.id);
                        }
                        break;
                        
                    case 'typing':
                        if (data.is_typing && data.user_id !== this.userId) {
                            this.showTypingIndicator();
                        } else {
                            this.hideTypingIndicator();
                        }
                        break;
                        
                    case 'message_read':
                        this.updateMessageReadStatus(data.message_id, data.read_by);
                        break;
                }
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket connection closed. Attempting to reconnect...');
            setTimeout(this.connectWebSocket, 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    // Load messages with pagination
    async loadMessages() {
        if (this.isLoading || !this.hasMore || !this.chatRequestId) return;
        
        this.isLoading = true;
        
        try {
            if (this.loadingMessages) {
                this.loadingMessages.style.display = 'block';
            }
            
            const response = await fetch(`/chat/room/${this.chatRequestId}/messages/?page=${this.currentPage}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error('Failed to load messages');
            
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                // If it's the first page, clear the loading indicator
                if (this.currentPage === 1 && this.messagesContainer) {
                    this.messagesContainer.innerHTML = '';
                }
                
                // Add messages to the DOM
                data.messages.forEach(message => {
                    this.addMessageToChat(message, message.sender_id === this.userId, true);
                });
                
                // Update pagination state
                this.hasMore = data.has_more;
                this.currentPage++;
                
                // Scroll to bottom if it's the first page
                if (this.currentPage === 2) {
                    this.scrollToBottom();
                }
            } else if (this.currentPage === 1 && this.messagesContainer) {
                // No messages at all
                this.messagesContainer.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-chat-square-text d-block mb-2" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        <p class="mb-0">No messages yet. Start the conversation!</p>
                    </div>
                `;
            }
            
            // Update load more button
            if (this.loadMoreBtn) {
                this.loadMoreBtn.style.display = this.hasMore ? 'block' : 'none';
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            
            if (this.messagesContainer) {
                this.messagesContainer.innerHTML = `
                    <div class="alert alert-danger">
                        Error loading messages. <button class="btn btn-sm btn-outline-danger" onclick="window.location.reload()">Retry</button>
                    </div>
                `;
            }
        } finally {
            this.isLoading = false;
            
            if (this.loadingMessages) {
                this.loadingMessages.style.display = 'none';
            }
        }
    }
    
    // Create a message element
    createMessageElement(message, isCurrentUser = false, prepend = false) {
        if (!this.messagesContainer) return null;
        
        const messageTime = new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        let messageContent = '';
        
        // Handle attachment if present
        if (message.attachment) {
            const fileExtension = message.attachment_name ? 
                message.attachment_name.split('.').pop().toLowerCase() : '';
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
    
    // Add a message to the chat
    addMessageToChat(message, isCurrentUser = false, prepend = false) {
        if (!this.messagesContainer) return null;
        
        // If it's the first message, clear the "no messages" placeholder
        if (this.messagesContainer.querySelector('.text-muted')) {
            this.messagesContainer.innerHTML = '';
        }
        
        const messageElement = this.createMessageElement(message, isCurrentUser, prepend);
        
        if (prepend && this.messagesContainer.firstChild) {
            this.messagesContainer.insertBefore(messageElement, this.messagesContainer.firstChild);
        } else {
            this.messagesContainer.appendChild(messageElement);
        }
        
        return messageElement;
    }
    
    // Mark a message as read
    markMessageAsRead(messageId) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                'type': 'read_receipt',
                'message_id': messageId
            }));
        }
    }
    
    // Update message read status in the UI
    updateMessageReadStatus(messageId, readBy) {
        if (!this.messagesContainer) return;
        
        const messageElement = this.messagesContainer.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const statusElement = messageElement.querySelector('.message-status');
            if (statusElement) {
                statusElement.innerHTML = '<i class="bi bi-check2-all"></i>';
                statusElement.classList.add('read');
            }
        }
    }
    
    // Handle message form submission
    async handleMessageSubmit(e) {
        e.preventDefault();
        
        if (!this.messageInput || !this.sendButton || !this.chatRequestId) return;
        
        const messageText = this.messageInput.value.trim();
        const attachmentFile = this.attachmentInput?.files[0];
        
        // Don't send empty messages
        if (!messageText && !attachmentFile) return;
        
        // If there's an attachment but no text, add a default message
        if (attachmentFile && !messageText) {
            this.messageInput.value = 'Sent an attachment';
            messageText = 'Sent an attachment';
        }
        
        // Disable form while sending
        this.sendButton.disabled = true;
        if (this.sendButtonIcon) this.sendButtonIcon.classList.add('d-none');
        if (this.sendingSpinner) this.sendingSpinner.classList.remove('d-none');
        
        try {
            // Show sending status
            this.showMessageStatus('sending');
            
            // Create FormData for the request
            const formData = new FormData();
            formData.append('message', messageText);
            formData.append('chat_request_id', this.chatRequestId);
            
            if (attachmentFile) {
                formData.append('attachment', attachmentFile);
            }
            
            // Send the message to the server
            const response = await fetch('/chat/send-message/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: formData
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            const data = await response.json();
            
            if (data.success) {
                // Add the message to the chat
                const messageElement = this.addMessageToChat(data.message, true);
                this.scrollToBottom();
                
                // If we have a WebSocket connection, send the message through it
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({
                        'type': 'chat_message',
                        'message': data.message
                    }));
                }
                
                // Mark as read after a short delay
                setTimeout(() => {
                    this.markMessageAsRead(data.message.id);
                }, 1000);
                
                // Show delivered status
                this.showMessageStatus('delivered');
                
                // Reset form
                this.messageInput.value = '';
                this.resetAttachmentPreview();
                
                // Reset input height
                this.messageInput.style.height = 'auto';
                
                // Focus back on input
                this.messageInput.focus();
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Show error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'alert alert-danger';
            errorMessage.textContent = 'Failed to send message. Please try again.';
            
            if (this.messagesContainer) {
                this.messagesContainer.appendChild(errorMessage);
            }
            
            // Show error status
            this.showMessageStatus('error');
        } finally {
            // Re-enable form
            this.sendButton.disabled = false;
            if (this.sendButtonIcon) this.sendButtonIcon.classList.remove('d-none');
            if (this.sendingSpinner) this.sendingSpinner.classList.add('d-none');
        }
    }
}

// Initialize the chat application when the DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chatApp = new ChatApp();
    });
} else {
    window.chatApp = new ChatApp();
}
