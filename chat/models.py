from django.db import models
from django.conf import settings
import os

class ChatRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    elder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_chat_requests')
    caregiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_chat_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        pass

    def __str__(self):
        return f"{self.elder} → {self.caregiver} ({self.status})"

def chat_attachment_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/chat_attachments/request_<id>/<filename>
    return f'chat_attachments/request_{instance.chat_request.id}/{filename}'

class ChatMessage(models.Model):
    chat_request = models.ForeignKey(ChatRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField(blank=True)
    attachment = models.FileField(upload_to=chat_attachment_path, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    @property
    def attachment_name(self):
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None
    
    @property
    def is_image(self):
        if self.attachment:
            ext = os.path.splitext(self.attachment.name)[1].lower()
            return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        return False
    
    @property
    def file_size(self):
        if self.attachment:
            try:
                return self.attachment.size
            except:
                return 0
        return 0
    
    @property
    def file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.1f} {unit}"
            size /= 1024
        return "0 B"

    def __str__(self):
        if self.message:
            return f"From {self.sender}: {self.message[:30]}..."
        elif self.attachment:
            return f"From {self.sender}: [Attachment: {self.attachment_name}]"
        return f"From {self.sender}: {self.message[:30]}..."
