from django.contrib import admin
from .models import Rating

class RatingAdmin(admin.ModelAdmin):
    list_display = ('caregiver', 'reviewer', 'stars', 'created_at')
    list_filter = ('stars', 'created_at', 'is_hidden', 'is_anonymous')
    search_fields = ('caregiver__username', 'reviewer__username', 'review_text')
    readonly_fields = ('caregiver', 'reviewer', 'stars', 'review_text', 'created_at')
    
    actions = ['hide_ratings', 'show_ratings']
    
    def hide_ratings(self, request, queryset):
        queryset.update(is_hidden=True)
    hide_ratings.short_description = "Hide selected ratings"
    
    def show_ratings(self, request, queryset):
        queryset.update(is_hidden=False)
    show_ratings.short_description = "Show selected ratings"

admin.site.register(Rating, RatingAdmin)
