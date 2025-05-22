from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from .models import AuditLog, Integration

User = get_user_model()

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'status', 'get_actions')
    list_filter = ('service_type', 'status')
    search_fields = ('name', 'service_type')
    readonly_fields = ('status',)
    
    def get_actions(self, obj):
        buttons = []
        if obj.status.lower() == 'connected':
            buttons.append(
                f'<a href="{reverse("admin:custom_admin_integration_test", args=[obj.id])}" '
                f'class="button" style="background: #417690; padding: 5px 10px; color: white; border-radius: 3px; margin-right: 5px;">Test</a>'
            )
            buttons.append(
                f'<a href="{reverse("admin:custom_admin_integration_disconnect", args=[obj.id])}" '
                f'class="button" style="background: #ba2121; padding: 5px 10px; color: white; border-radius: 3px;">Disconnect</a>'
            )
        else:
            buttons.append(
                f'<a href="{reverse("admin:custom_admin_integration_connect", args=[obj.id])}" '
                f'class="button" style="background: #417690; padding: 5px 10px; color: white; border-radius: 3px;">Connect</a>'
            )
        return mark_safe(' '.join(buttons))
    get_actions.short_description = 'Actions'
    get_actions.allow_tags = True

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_display', 'action_short', 'details_short')
    list_filter = ('timestamp',)
    search_fields = ('user__username', 'user__email', 'action', 'details')
    readonly_fields = ('timestamp', 'user', 'action', 'details')
    date_hierarchy = 'timestamp'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name() or obj.user.email} ({obj.user.username})"
        return "System"
    user_display.short_description = 'User'
    
    def action_short(self, obj):
        return obj.action[:50] + '...' if len(obj.action) > 50 else obj.action
    action_short.short_description = 'Action'
    
    def details_short(self, obj):
        if obj.details:
            return obj.details[:100] + '...' if len(obj.details) > 100 else obj.details
        return "-"
    details_short.short_description = 'Details'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
