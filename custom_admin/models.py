from django.db import models
from django.conf import settings

class Integration(models.Model):
    SERVICE_CHOICES = [
        ('sendgrid', 'SendGrid'),
        ('twilio', 'Twilio'),
        # Add more as needed
    ]
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    status = models.CharField(max_length=20, default='Not Connected')
    config = models.JSONField(default=dict, blank=True)  # Store API keys, etc.

    class Meta:
        app_label = 'custom_admin'

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_audit_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.user}: {self.action}"

class Article(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

