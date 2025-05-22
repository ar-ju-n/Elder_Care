"""
Authentication views for the custom admin interface.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@require_http_methods(["GET", "POST"])
def custom_admin_login(request):
    """
    Custom admin login view that enforces admin privileges.
    """
    # If user is already authenticated and is an admin, redirect to dashboard
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'You do not have permission to access the admin panel.')
            return redirect('landing')  # Redirect to the main landing page
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and is_admin(user):
            login(request, user)
            messages.success(request, 'Successfully logged in to admin panel.')
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'custom_admin/login.html')
