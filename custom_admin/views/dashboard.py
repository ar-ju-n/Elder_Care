"""
Dashboard views for the custom admin interface.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone

# Import models
from accounts.models import User
from events.models import Event
from jobs.models import Job, Application

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
def dashboard(request):
    """
    Main dashboard view for the admin interface.
    Shows key metrics and recent activities.
    """
    if not is_admin(request.user):
        return redirect('/')  # Or your permission denied page
    
    # Get user statistics
    total_users = User.objects.count()
    new_users_today = User.objects.filter(
        date_joined__date=timezone.now().date()
    ).count()
    
    # Get job statistics
    total_jobs = Job.objects.count()
    open_jobs = Job.objects.filter(status='open').count()
    total_applications = Application.objects.count()
    
    # Get recent events
    recent_events = Event.objects.order_by('-start_time')[:5]
    
    context = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'total_jobs': total_jobs,
        'open_jobs': open_jobs,
        'total_applications': total_applications,
        'recent_events': recent_events,
    }
    
    return render(request, 'custom_admin/dashboard.html', context)
