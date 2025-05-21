from django.contrib import admin
from .models import SystemSetting, AuditLog, NotificationTemplate, ScheduledNotification, BrandingSetting

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'target_type', 'target_repr')
    list_filter = ('action', 'target_type')
    search_fields = ('target_repr', 'details')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_by', 'created_at')
    search_fields = ('name', 'subject', 'body')

@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'scheduled_for', 'created_by', 'sent', 'sent_at')
    list_filter = ('sent',)
    search_fields = ('subject', 'body')

@admin.register(BrandingSetting)
class BrandingSettingAdmin(admin.ModelAdmin):
    list_display = ('theme', 'contact_email', 'logo')
