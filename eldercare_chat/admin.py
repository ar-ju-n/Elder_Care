from django.contrib import admin
from .models import Assignment, Chat, Message, Skill, CaregiverSkill

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('elderly', 'caregiver', 'active', 'assigned_at')
    list_filter = ('active', 'assigned_at')
    search_fields = ('elderly__username', 'caregiver__username')

admin.site.register(Assignment, AssignmentAdmin)

class ChatAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('assignment__elderly__username', 'assignment__caregiver__username')

admin.site.register(Chat, ChatAdmin)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat', 'timestamp', 'is_admin_viewed')
    list_filter = ('timestamp', 'is_admin_viewed')
    search_fields = ('sender__username', 'content')
    readonly_fields = ('sender', 'chat', 'content', 'timestamp')

admin.site.register(Message, MessageAdmin)

class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

admin.site.register(Skill, SkillAdmin)

class CaregiverSkillAdmin(admin.ModelAdmin):
    list_display = ('caregiver', 'skill', 'years_experience')
    list_filter = ('skill', 'years_experience')
    search_fields = ('caregiver__username', 'skill__name')

admin.site.register(CaregiverSkill, CaregiverSkillAdmin)
