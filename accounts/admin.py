from django.contrib import admin
from .models import User, AccountDeletionRequest
from django.utils import timezone

# We're registering User in custom_admin/admin.py, so we don't need to register it here
# This prevents duplicate registration

@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_at', 'approved', 'processed_at')
    actions = ['approve_deletion']

    def approve_deletion(self, request, queryset):
        for deletion_request in queryset.filter(approved=False):
            user = deletion_request.user
            user.delete()
            deletion_request.approved = True
            deletion_request.processed_at = timezone.now()
            deletion_request.save()
    approve_deletion.short_description = "Approve and delete selected accounts"
