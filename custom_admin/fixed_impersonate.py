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
        
        # Use the custom_admin AuditLog model directly
        from custom_admin.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action=f"Impersonated user {target_user.username}",
            details=f"Admin {request.user.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('landing')
