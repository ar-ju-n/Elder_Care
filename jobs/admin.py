from django.contrib import admin
from .models import Job, Application

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'posted_by', 'approved', 'created_at')
    list_filter = ('approved', 'created_at')
    search_fields = ('title', 'description', 'location', 'posted_by__username')
    
    actions = ['approve_jobs', 'reject_jobs']
    
    def approve_jobs(self, request, queryset):
        queryset.update(approved=True)
    approve_jobs.short_description = "Approve selected jobs"
    
    def reject_jobs(self, request, queryset):
        queryset.update(approved=False)
    reject_jobs.short_description = "Reject selected jobs"

admin.site.register(Job, JobAdmin)

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'caregiver', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job__title', 'caregiver__username', 'cover_letter')

admin.site.register(Application, ApplicationAdmin)
