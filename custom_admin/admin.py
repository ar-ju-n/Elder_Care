from django.contrib import admin
from .models import Article
from content.models import Link

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'body')
    list_filter = ('created_at',)

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'description', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'url')
    list_filter = ('created_at',)

# Register your models here.
