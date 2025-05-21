"""
Utility functions for handling audit logging in the custom_admin app.
This helps resolve conflicts between multiple AuditLog models in the project.
"""
from django.contrib.auth import get_user_model

User = get_user_model()

def create_audit_log(user, action, details=None, **kwargs):
    """
    Create an audit log entry using the appropriate AuditLog model.
    This function handles the differences between the two AuditLog models in the project.
    
    Args:
        user: The user performing the action
        action: A description of the action
        details: Additional details about the action
        **kwargs: Additional fields for the core AuditLog model if needed
    """
    # Import the models here to avoid circular imports
    from custom_admin.models import AuditLog as CustomAdminAuditLog
    
    # Create an audit log entry using the custom_admin AuditLog model
    CustomAdminAuditLog.objects.create(
        user=user,
        action=action,
        details=details or ''
    )
    
    # If you need to also log to the core AuditLog model, you can do that here
    # Uncomment this if needed
    # try:
    #     from core.models import AuditLog as CoreAuditLog
    #     CoreAuditLog.objects.create(
    #         user=user,
    #         action=kwargs.get('action_type', 'edit'),
    #         target_type=kwargs.get('target_type', ''),
    #         target_id=kwargs.get('target_id', 0),
    #         target_repr=kwargs.get('target_repr', ''),
    #         details=details or ''
    #     )
    # except (ImportError, AttributeError):
    #     pass  # If the core AuditLog model isn't available, just skip it
