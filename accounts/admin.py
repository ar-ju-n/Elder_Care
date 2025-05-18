from django.contrib import admin
from .models import User, AccountDeletionRequest, CaregiverVerification
from django.utils import timezone

# We're registering User in custom_admin/admin.py, so we don't need to register it here
# This prevents duplicate registration

from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages

@admin.register(CaregiverVerification)
class CaregiverVerificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'government_id_number', 'certification_type', 'submitted_at', 'reviewed', 'approved', 'reviewed_at', 'admin_comment'
    )
    readonly_fields = ('user', 'government_id_number', 'certification_type', 'document', 'submitted_at', 'reviewed', 'approved', 'reviewed_at')
    search_fields = ('user__username', 'user__email', 'government_id_number', 'certification_type')
    list_filter = ('reviewed', 'approved', 'submitted_at')
    actions = None  # Remove all bulk actions
    change_form_template = 'accounts/caregiververification/change_form.html'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.process_approve), name='accounts_caregiververification_approve'),
            path('<path:object_id>/decline/', self.admin_site.admin_view(self.process_decline), name='accounts_caregiververification_decline'),
        ]
        return custom_urls + urls

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        context['show_approve_decline'] = obj and not obj.reviewed and request.user.is_superuser
        return super().render_change_form(request, context, *args, **kwargs)

    def process_approve(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj and not obj.reviewed and request.user.is_superuser:
            obj.reviewed = True
            obj.approved = True
            obj.reviewed_at = timezone.now()
            obj.admin_comment = 'Approved by admin.'
            obj.save()
            self.message_user(request, "Caregiver verification approved.", messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    def process_decline(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj and not obj.reviewed and request.user.is_superuser:
            obj.reviewed = True
            obj.approved = False
            obj.reviewed_at = timezone.now()
            if not obj.admin_comment:
                obj.admin_comment = 'Declined by admin.'
            obj.save()
            self.message_user(request, "Caregiver verification declined.", messages.WARNING)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages

@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_at', 'approved', 'processed_at')
    readonly_fields = ('user', 'requested_at', 'approved', 'processed_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('approved', 'requested_at')
    actions = None  # Remove all bulk actions
    change_form_template = 'admin/accounts/accountdeletionrequest/change_form.html'

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.process_approve), name='accounts_accountdeletionrequest_approve'),
            path('<path:object_id>/decline/', self.admin_site.admin_view(self.process_decline), name='accounts_accountdeletionrequest_decline'),
        ]
        return custom_urls + urls

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get('original')
        context['show_approve_decline'] = obj and not obj.approved and request.user.is_superuser
        return super().render_change_form(request, context, *args, **kwargs)

    def process_approve(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj and not obj.approved and request.user.is_superuser:
            user = obj.user
            user.delete()
            obj.approved = True
            obj.processed_at = timezone.now()
            obj.save()
            self.message_user(request, "Account deletion request approved and user deleted.", messages.SUCCESS)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

    def process_decline(self, request, object_id):
        obj = self.get_object(request, object_id)
        if obj and not obj.approved and request.user.is_superuser:
            obj.approved = False
            obj.processed_at = timezone.now()
            obj.save()
            self.message_user(request, "Account deletion request declined.", messages.WARNING)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))
