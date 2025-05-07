from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatbotLog(models.Model):
    """Model to store chatbot interactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    user_message = models.TextField()
    bot_response = models.TextField()
    reviewed_by_admin = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Chatbot Log'
        verbose_name_plural = 'Chatbot Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class ChatbotSettings(models.Model):
    """Model to store chatbot settings"""
    api_key = models.CharField(max_length=255, blank=True, help_text="OpenAI API Key")
    model = models.CharField(max_length=50, default="gpt-4o-mini", help_text="OpenAI model to use")
    
    class Meta:
        verbose_name = 'Chatbot Settings'
        verbose_name_plural = 'Chatbot Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and ChatbotSettings.objects.exists():
            # Update existing instance
            settings_obj = ChatbotSettings.objects.first()
            settings_obj.api_key = self.api_key
            settings_obj.model = self.model
            settings_obj.save()
            return settings_obj
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_api_key(cls):
        """Get API key from settings or environment"""
        from django.conf import settings as django_settings
        
        # First try to get from model
        try:
            settings_obj = cls.objects.first()
            if settings_obj and settings_obj.api_key:
                return settings_obj.api_key
        except:
            pass
        
        # Then try environment variables or settings.py
        return getattr(django_settings, "OPENAI_API_KEY", "")
    
    @classmethod
    def get_model(cls):
        """Get model name from settings"""
        try:
            settings_obj = cls.objects.first()
            if settings_obj and settings_obj.model:
                return settings_obj.model
        except:
            pass
        
        return "gpt-4o-mini"
