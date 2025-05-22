def user_context(request):
    from .models import User
    
    context = {
        'user_roles': {
            'is_admin': False,
            'is_caregiver': False,
            'is_family': False,
            'is_authenticated': False
        },
        'permissions': {
            'can_manage_content': False,
            'can_manage_jobs': False,
            'can_apply_for_jobs': False,
            'can_manage_forum': False,
            'can_participate_in_forum': False
        },
        'emergency_contacts': [],
        'pending_connection_requests_count': 0,
        'user_data': {
            'isAuthenticated': False
        }
    }
    
    if request.user.is_authenticated:
        pending_requests_count = 0
        if request.user.role == User.CAREGIVER:
            pending_requests_count = request.user.received_connection_requests.filter(status='pending').count()
        
        # Add available_users for universal chat modal
        from .models import User as UserModel
        context['available_users'] = UserModel.objects.exclude(id=request.user.id)
        # Update role information
        context['user_roles'].update({
            'is_admin': request.user.role == User.ADMIN,
            'is_caregiver': request.user.role == User.CAREGIVER,
            'is_family': request.user.role == User.FAMILY,
            'is_authenticated': True
        })
        
        # Update permissions based on role
        context['permissions'].update({
            'can_manage_content': request.user.role == User.ADMIN,
            'can_manage_jobs': request.user.role in [User.ADMIN, User.FAMILY],
            'can_apply_for_jobs': request.user.role == User.CAREGIVER,
            'can_manage_forum': request.user.role in [User.ADMIN, User.FAMILY],
            'can_participate_in_forum': True  # All roles can participate
        })
        
        # Add user-specific data
        context.update({
            'emergency_contacts': request.user.emergency_contacts.all(),
            'pending_connection_requests_count': pending_requests_count,
            'user_data': {
                'isAuthenticated': True,
                'userId': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'role': request.user.role,
                'full_name': request.user.get_full_name()
            }
        })
    
    return context
