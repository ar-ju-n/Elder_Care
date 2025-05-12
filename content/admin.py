from django.contrib import admin
from .models import Article, Tag, Video

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_by', 'published_at', 'image')
    list_filter = ('published_at', 'tags')
    search_fields = ('title', 'body', 'published_by__username', 'image')
    filter_horizontal = ('tags',)
    
    actions = ['publish_articles', 'unpublish_articles']
    
    def publish_articles(self, request, queryset):
        queryset.update(is_published=True)
    publish_articles.short_description = "Publish selected articles"
    
    def unpublish_articles(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_articles.short_description = "Unpublish selected articles"

admin.site.register(Article, ArticleAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Tag, TagAdmin)

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_by', 'published_at', 'file')
    list_filter = ('published_at', 'tags')
    search_fields = ('title', 'url', 'published_by__username', 'file')
    filter_horizontal = ('tags',)

admin.site.register(Video, VideoAdmin)
