from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('reply', 'Reply'),
        ('mention', 'Mention'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    url = models.CharField(max_length=255)
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:40]}..."

def broadcast_notification(user_id, unread_count):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user_id}",
        {
            "type": "send.notification",
            "data": {
                "type": "notification",
                "unread_count": unread_count,
            }
        }
    )

class Topic(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics', null=True, blank=True)
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_topics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Reply(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='replies')
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_replies')
    created_at = models.DateTimeField(auto_now_add=True)
    is_best_answer = models.BooleanField(default=False)

    def __str__(self):
        return f"Reply by {self.author} on {self.topic}"

class ReplyUpvote(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='upvotes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reply', 'user')

    def __str__(self):
        return f"Upvote by {self.user} on reply {self.reply.id}"
# Create your models here.
