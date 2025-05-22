from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from .models import User

def role_required(*roles):
    """
    Decorator for views that checks that the user has the required role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect(f"{reverse_lazy('login')}?next={request.path}")
                
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Decorator for views that require admin role."""
    return role_required(User.ADMIN)(view_func)

def caregiver_required(view_func):
    """Decorator for views that require caregiver role."""
    return role_required(User.CAREGIVER)(view_func)

def family_required(view_func):
    """Decorator for views that require family role."""
    return role_required(User.FAMILY)(view_func)

def admin_or_family_required(view_func):
    """Decorator for views that require either admin or family role."""
    return role_required(User.ADMIN, User.FAMILY)(view_func)

def permission_required(permission_name):
    """
    Decorator for views that checks if the user has the specified permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from .utils import get_permitted_actions
            
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect(f"{reverse_lazy('login')}?next={request.path}")
                
            permissions = get_permitted_actions(request.user)
            if not permissions.get(permission_name, False):
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
