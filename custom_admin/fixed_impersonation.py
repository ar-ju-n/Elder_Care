"""
FIXED IMPERSONATION FUNCTION

Copy and paste this function into your views.py file to replace both existing
impersonate_user functions (around lines 1356 and 1679).

This version fixes the login redirect issue by:
1. Setting the authentication backend explicitly
2. Adding a session flag for impersonation
3. Using the correct AuditLog model
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
        target_user.backend = 'django.contrib.auth.backends.ModelBackend'
        
        # Login as the target user
        login(request, target_user)
        
        # Add a session flag to indicate this is an impersonation session
        request.session['is_impersonating'] = True
        
        messages.info(request, f"You are now impersonating {target_user.get_full_name() or target_user.username}.")
        
        # Use the custom_admin AuditLog model directly
        from custom_admin.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action=f"Impersonated user {target_user.username}",
            details=f"Admin {request.user.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
        
        # Redirect to the home page or dashboard
        return redirect('landing')
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('custom_admin:user_management')


"""
ALSO UPDATE THE stop_impersonation FUNCTION

Replace your current stop_impersonation function with this one:
"""

@login_required
def stop_impersonation(request):
    orig_id = request.session.pop('impersonate_original_id', None)
    # Also remove the impersonation flag
    request.session.pop('is_impersonating', None)
    
    if orig_id:
        try:
            original_user = User.objects.get(id=orig_id)
            # Set the backend for the original user
            original_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, original_user)
            messages.info(request, "You have stopped impersonating and returned to your admin account.")
            
            # Log the action
            from custom_admin.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action="Stopped impersonation",
                details=f"Admin returned to their original account"
            )
            
            return redirect('custom_admin:dashboard')
        except User.DoesNotExist:
            messages.error(request, "Original user not found.")
    else:
        messages.warning(request, "You were not impersonating anyone.")
    
    return redirect('landing')
