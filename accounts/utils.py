from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import User

def check_role(user, *roles):
    """Check if the user has any of the specified roles."""
    if not user.is_authenticated:
        return False
    return user.role in roles

def admin_required(user):
    """Check if the user is an admin."""
    return check_role(user, User.ADMIN)

def caregiver_required(user):
    """Check if the user is a caregiver."""
    return check_role(user, User.CAREGIVER)

def family_required(user):
    """Check if the user is a family member."""
    return check_role(user, User.FAMILY)

def admin_or_family_required(user):
    """Check if the user is an admin or family member."""
    return check_role(user, User.ADMIN, User.FAMILY)

def can_manage_content(user):
    """Check if the user can manage content (admin only)."""
    return admin_required(user)

def can_manage_jobs(user):
    """Check if the user can manage jobs (admin or family)."""
    return admin_or_family_required(user)

def can_apply_for_jobs(user):
    """Check if the user can apply for jobs (caregiver)."""
    return caregiver_required(user)

def can_manage_forum(user):
    """Check if the user can manage forum (admin or family)."""
    return admin_or_family_required(user)

def can_participate_in_forum(user):
    """Check if the user can participate in forum (all roles)."""
    return user.is_authenticated

def can_manage_events(user):
    """Check if the user can manage events (admin or family)."""
    return admin_or_family_required(user)

def can_manage_caregiver_verification(user):
    """Check if the user can manage caregiver verification (admin only)."""
    return admin_required(user)

def get_permitted_actions(user):
    """Get a dictionary of all permissions for the user."""
    return {
        'can_manage_content': can_manage_content(user),
        'can_manage_jobs': can_manage_jobs(user),
        'can_apply_for_jobs': can_apply_for_jobs(user),
        'can_manage_forum': can_manage_forum(user),
        'can_participate_in_forum': can_participate_in_forum(user),
        'can_manage_events': can_manage_events(user),
        'can_manage_caregiver_verification': can_manage_caregiver_verification(user),
    }
