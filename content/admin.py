from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Article, Video, HomepageSlide, Link, Guide, FAQ, Tag

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'article_count', 'video_count', 'guide_count', 'faq_count')
    search_fields = ('name',)
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Articles'
    
    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Videos'
    
    def guide_count(self, obj):
        return obj.guides.count()
    guide_count.short_description = 'Guides'
    
    def faq_count(self, obj):
        return obj.faqs.count()
    faq_count.short_description = 'FAQs'

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_display', 'published_at', 'updated_at', 'tag_list')
    list_filter = ('published_at', 'tags')
    search_fields = ('title', 'body', 'author__first_name', 'author__last_name', 'author__email')
    readonly_fields = ('published_at', 'updated_at')
    filter_horizontal = ('tags',)
    
    def author_display(self, obj):
        if obj.author:
            return f"{obj.author.get_full_name() or obj.author.email}"
        return "-"
    author_display.short_description = 'Author'
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    tag_list.short_description = 'Tags'

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_by_display', 'published_at', 'tag_list')
    list_filter = ('published_at', 'tags')
    search_fields = ('title', 'published_by__first_name', 'published_by__last_name', 'published_by__email')
    readonly_fields = ('published_at',)
    filter_horizontal = ('tags',)
    
    def published_by_display(self, obj):
        if obj.published_by:
            return f"{obj.published_by.get_full_name() or obj.published_by.email}"
        return "-"
    published_by_display.short_description = 'Published By'
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    tag_list.short_description = 'Tags'

class HomepageSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'preview_image', 'ordering', 'has_link')
    list_editable = ('ordering',)
    list_filter = ('ordering',)
    search_fields = ('title', 'description')
    
    def preview_image(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px;" />')
        return "No Image"
    preview_image.short_description = 'Preview'
    preview_image.allow_tags = True
    
    def has_link(self, obj):
        return bool(obj.link)
    has_link.boolean = True
    has_link.short_description = 'Has Link?'

class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url_display', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'url')
    readonly_fields = ('created_at', 'updated_at')
    
    def url_display(self, obj):
        return format_html('<a href="{0}" target="_blank">{0}</a>', obj.url)
    url_display.short_description = 'URL'
    url_display.allow_tags = True

class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_by_display', 'published_at', 'updated_at', 'tag_list')
    list_filter = ('published_at', 'tags')
    search_fields = ('title', 'content', 'published_by__first_name', 'published_by__last_name')
    readonly_fields = ('published_at', 'updated_at')
    filter_horizontal = ('tags',)
    
    def published_by_display(self, obj):
        if obj.published_by:
            return f"{obj.published_by.get_full_name() or obj.published_by.email}"
        return "-"
    published_by_display.short_description = 'Published By'
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    tag_list.short_description = 'Tags'

class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'short_answer', 'tag_list', 'created_at', 'updated_at')
    list_filter = ('created_at', 'tags')
    search_fields = ('question', 'answer')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags',)
    
    def short_answer(self, obj):
        return f"{obj.answer[:100]}..." if len(obj.answer) > 100 else obj.answer
    short_answer.short_description = 'Answer'
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    tag_list.short_description = 'Tags'

# Register models
admin.site.register(Tag, TagAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(HomepageSlide, HomepageSlideAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Guide, GuideAdmin)
admin.site.register(FAQ, FAQAdmin)
