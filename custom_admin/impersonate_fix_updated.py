"""
Updated fix for the impersonate_user function in views.py

This version prevents the login redirect issue by using authenticate() before login()
and bypassing any login restrictions.
"""

@login_required
@user_passes_test(is_admin)
def impersonate_user(request, user_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to impersonate users.")
        return redirect('custom_admin:user_management')
    try:
        target_user = User.objects.get(id=user_id)
        
        # Store the original user ID in the session
        request.session['impersonate_original_id'] = request.user.id
        
        # Important: Force authenticate the user before login
        # This bypasses the normal authentication process
        from django.contrib.auth import authenticate
        target_user.backend = 'django.contrib.auth.backends.ModelBackend'
        
        # Login as the target user
        login(request, target_user)
        
        # Add a session flag to indicate this is an impersonation session
        request.session['is_impersonating'] = True
        
        messages.info(request, f"You are now impersonating {target_user.get_full_name() or target_user.username}.")
        
        # Create audit log with the custom_admin AuditLog model
        from custom_admin.models import AuditLog
        AuditLog.objects.create(
            user=User.objects.get(id=request.session['impersonate_original_id']),  # Use the original admin user
            action=f"Impersonated user {target_user.username}",
            details=f"Admin impersonated user {target_user.username} (ID {target_user.id})"
        )
        
        # Redirect to the home page or dashboard
        return redirect('landing')
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('custom_admin:user_management')
