from django.contrib import admin

from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'location', 'created_by', 'created_at')
    search_fields = ('title', 'description', 'location')
    list_filter = ('start_time',)

