"""
Fix for the impersonate_user function in views.py

Replace the impersonate_user function in views.py with this implementation
that uses the correct AuditLog model from custom_admin.models.
"""

# This is the correct implementation of the impersonate_user function
# that works with the custom_admin AuditLog model

@login_required
@user_passes_test(is_admin)
def impersonate_user(request, user_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to impersonate users.")
        return redirect('custom_admin:user_management')
    try:
        target_user = User.objects.get(id=user_id)
        request.session['impersonate_original_id'] = request.user.id
        login(request, target_user)
        messages.info(request, f"You are now impersonating {target_user.get_full_name() or target_user.username}.")
        
        # Import and use the custom_admin AuditLog model directly
        from custom_admin.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action=f"Impersonated user {target_user.username}",
            details=f"Admin {request.user.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('landing')

"""
Instructions to fix the issue:

1. Open views.py in the custom_admin app
2. Find both impersonate_user functions (around lines 1356 and 1679)
3. Delete both functions completely
4. Add the above implementation of impersonate_user in their place
5. Make sure to keep only ONE implementation of the function

This will fix the issue with the AuditLog model fields not matching.
"""
