from django.contrib import admin

from .models import Topic, Reply, Category, Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notif_type', 'is_read', 'created_at', 'message')
    list_filter = ('notif_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'author__username')
    list_filter = ('created_at', 'category')

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'created_at')
    search_fields = ('body', 'author__username')
    list_filter = ('created_at',)
