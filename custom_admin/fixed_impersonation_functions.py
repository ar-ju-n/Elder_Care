# FIXED IMPERSONATION FUNCTIONS
# Copy and paste these functions into your views.py file to replace the existing ones

# Replace the impersonate_user function at line 1355-1374
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
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='edit',
            target_type='user',
            target_id=target_user.id,
            target_repr=target_user.username,
            details=f"Admin {request.user.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
        
        # Redirect to the home page or dashboard
        return redirect('landing')
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('custom_admin:user_management')

# Replace the stop_impersonation function at line 1377-1399
@login_required
def stop_impersonation(request):
    orig_id = request.session.pop('impersonate_original_id', None)
    # Also remove the impersonation flag
    request.session.pop('is_impersonating', None)
    
    User = get_user_model()
    if orig_id:
        try:
            orig_user = User.objects.get(id=orig_id)
            # Set the backend for the original user
            orig_user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, orig_user)
            messages.info(request, "You have stopped impersonating and are now yourself again.")
            AuditLog.objects.create(
                user=orig_user,
                action='edit',
                target_type='user',
                target_id=request.user.id,
                target_repr=request.user.username,
                details=f"Admin {orig_user.username} stopped impersonating user {request.user.username} (ID {request.user.id})"
            )
        except User.DoesNotExist:
            logout(request)
            messages.warning(request, "Original admin user not found. Please log in again.")
    else:
        logout(request)
        messages.warning(request, "Impersonation session not found. Please log in again.")
    return redirect('custom_admin:user_management')

# Replace the second impersonate_user function at line 1678-1697
# with the same implementation as above

# Replace the second stop_impersonation function at line 1652-1670
# with the same implementation as above
