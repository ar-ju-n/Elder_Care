"""
Signals for the custom_admin app.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditLog

@receiver([post_save, post_delete])
def log_model_changes(sender, **kwargs):
    """
    Log changes to models in the AuditLog.
    """
    # Skip if the model being saved is AuditLog itself to prevent recursion
    if sender == AuditLog:
        return
        
    instance = kwargs.get('instance')
    created = kwargs.get('created', False)
    
    # Determine the action type
    if 'created' in kwargs:
        if created:
            action = f"Created {sender._meta.verbose_name}"
        else:
            action = f"Updated {sender._meta.verbose_name}"
    else:
        action = f"Deleted {sender._meta.verbose_name}"
    
    # Get the user if available
    user = None
    if hasattr(instance, 'user'):
        user = instance.user
    elif hasattr(instance, 'created_by'):
        user = instance.created_by
    
    # Only log if the instance has an 'id' attribute (skip e.g. Session)
    if not hasattr(instance, 'id'):
        return
    AuditLog.objects.create(
        user=user,
        action=action,
        details=f"{sender._meta.verbose_name} {instance.id} was {action.lower()}"
    )
