from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User

class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin to check if the user has the required role.
    """
    roles_required = []
    permission_denied_message = "You don't have permission to access this page."
    login_url = reverse_lazy('login')
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.role in self.roles_required
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('home')

class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin to check if the user is an admin."""
    roles_required = [User.ADMIN]
    permission_denied_message = "Only administrators can access this page."

class CaregiverRequiredMixin(RoleRequiredMixin):
    """Mixin to check if the user is a caregiver."""
    roles_required = [User.CAREGIVER]
    permission_denied_message = "This page is only accessible to caregivers."

class FamilyRequiredMixin(RoleRequiredMixin):
    """Mixin to check if the user is a family member."""
    roles_required = [User.FAMILY]
    permission_denied_message = "This page is only accessible to family members."

class AdminOrFamilyMixin(RoleRequiredMixin):
    """Mixin to check if the user is an admin or family member."""
    roles_required = [User.ADMIN, User.FAMILY]
    permission_denied_message = "This page is only accessible to administrators and family members."

class ContentManagementMixin(AdminRequiredMixin):
    """Mixin for content management views (admin only)."""
    pass

class JobManagementMixin(AdminOrFamilyMixin):
    """Mixin for job management views (admin and family)."""
    pass

class ForumManagementMixin(AdminOrFamilyMixin):
    """Mixin for forum management views (admin and family)."""
    pass

class EventManagementMixin(AdminOrFamilyMixin):
    """Mixin for event management views (admin and family)."""
    pass

class CaregiverVerificationMixin(AdminRequiredMixin):
    """Mixin for caregiver verification views (admin only)."""
    pass
