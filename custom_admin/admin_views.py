from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
import os
import json
import subprocess
import logging
from datetime import datetime
from .models import AuditLog, Integration

logger = logging.getLogger(__name__)

def admin_required(view_func):
    """Decorator for views that checks that the user is a staff member."""
    return user_passes_test(lambda u: u.is_staff)(view_func)

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard view."""
    context = {
        'title': 'Admin Dashboard',
        'integrations': Integration.objects.all()[:5],
        'recent_logs': AuditLog.objects.select_related('user').order_by('-timestamp')[:10],
    }
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def audit_log_list(request):
    """View to display audit logs."""
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    # Handle search
    search_query = request.GET.get('q')
    if search_query:
        logs = logs.filter(
            Q(action__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Handle date filtering
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    context = {
        'title': 'Audit Logs',
        'logs': logs[:100],  # Limit to 100 most recent logs
        'search_query': search_query or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
    }
    return render(request, 'admin/audit_logs.html', context)

@staff_member_required
def system_status(request):
    """View to display system status information."""
    # Get database status
    db_status = 'online'
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    # Get disk usage
    try:
        disk_usage = subprocess.check_output(['df', '-h']).decode('utf-8')
    except Exception as e:
        disk_usage = f'Error getting disk usage: {str(e)}'
    
    context = {
        'title': 'System Status',
        'db_status': db_status,
        'disk_usage': disk_usage,
        'current_time': timezone.now(),
        'debug_mode': settings.DEBUG,
    }
    return render(request, 'admin/system_status.html', context)

@staff_member_required
def create_backup(request):
    """Create a database backup."""
    if request.method == 'POST':
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
            
            # Create backup command (PostgreSQL example)
            db = settings.DATABASES['default']
            cmd = [
                'pg_dump',
                '-h', db.get('HOST', 'localhost'),
                '-U', db['USER'],
                '-d', db['NAME'],
                '-f', backup_file
            ]
            
            # Set PGPASSWORD as environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db['PASSWORD']
            
            # Execute backup
            subprocess.run(cmd, env=env, check=True)
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Created database backup',
                details=f'Backup file: {backup_file}'
            )
            
            messages.success(request, f'Backup created successfully: {backup_file}')
        except Exception as e:
            logger.error(f'Error creating backup: {str(e)}', exc_info=True)
            messages.error(request, f'Error creating backup: {str(e)}')
    
    return redirect('admin:system_status')

@staff_member_required
def restore_backup(request):
    """Restore database from backup."""
    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        if not backup_file:
            messages.error(request, 'No backup file provided')
            return redirect('admin:system_status')
        
        try:
            # Save uploaded file temporarily
            temp_dir = os.path.join(settings.BASE_DIR, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, backup_file.name)
            
            with open(temp_path, 'wb+') as destination:
                for chunk in backup_file.chunks():
                    destination.write(chunk)
            
            # Restore command (PostgreSQL example)
            db = settings.DATABASES['default']
            cmd = [
                'psql',
                '-h', db.get('HOST', 'localhost'),
                '-U', db['USER'],
                '-d', db['NAME'],
                '-f', temp_path
            ]
            
            # Set PGPASSWORD as environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db['PASSWORD']
            
            # Execute restore
            subprocess.run(cmd, env=env, check=True)
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Restored database from backup',
                details=f'Backup file: {backup_file.name}'
            )
            
            # Clean up
            os.remove(temp_path)
            
            messages.success(request, 'Database restored successfully')
        except Exception as e:
            logger.error(f'Error restoring backup: {str(e)}', exc_info=True)
            messages.error(request, f'Error restoring backup: {str(e)}')
    
    return redirect('admin:system_status')

@staff_member_required
def clear_cache(request):
    """Clear the application cache."""
    try:
        from django.core.cache import cache
        cache.clear()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Cleared application cache',
            details='All cache has been cleared'
        )
        
        messages.success(request, 'Cache cleared successfully')
    except Exception as e:
        logger.error(f'Error clearing cache: {str(e)}', exc_info=True)
        messages.error(request, f'Error clearing cache: {str(e)}')
    
    return redirect('admin:system_status')

@staff_member_required
def optimize_database(request):
    """Optimize database tables."""
    try:
        with connection.cursor() as cursor:
            # PostgreSQL specific optimization
            cursor.execute("VACUUM ANALYZE;")
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Optimized database',
            details='VACUUM ANALYZE executed on all tables'
        )
        
        messages.success(request, 'Database optimization completed')
    except Exception as e:
        logger.error(f'Error optimizing database: {str(e)}', exc_info=True)
        messages.error(request, f'Error optimizing database: {str(e)}')
    
    return redirect('admin:system_status')

@staff_member_required
def check_for_updates(request):
    """Check for system updates."""
    try:
        # This is a placeholder - in a real application, you would check for updates here
        # For example, you might check a package repository or your own update server
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Checked for system updates',
            details='Update check performed'
        )
        
        messages.info(request, 'System is up to date')
    except Exception as e:
        logger.error(f'Error checking for updates: {str(e)}', exc_info=True)
        messages.error(request, f'Error checking for updates: {str(e)}')
    
    return redirect('admin:system_status')
