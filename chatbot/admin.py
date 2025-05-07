from django.contrib import admin
from .models import ChatbotLog, ChatbotSettings

class ChatbotLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'user_message', 'bot_response')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'user_message', 'bot_response')
    readonly_fields = ('user', 'timestamp', 'user_message', 'bot_response')

admin.site.register(ChatbotLog, ChatbotLogAdmin)

class ChatbotSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'model')
    fields = ('api_key', 'model')
    
    def has_add_permission(self, request):
        # Only allow adding if no settings exist
        return not ChatbotSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ChatbotSettings, ChatbotSettingsAdmin)
