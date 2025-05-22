"""
System Management Views for Custom Admin
"""
import os
import json
import psutil
import platform
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.db import connection, transaction
from django.db.models import Count
import time

from core.models import SystemSetting, AuditLog, NotificationTemplate
from core.forms import SystemSettingForm

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def maintenance_management(request):
    """
    Main maintenance management dashboard that provides an overview of system maintenance tasks.
    """
    # Get system information for the dashboard
    system_info = {
        'os': f"{platform.system()} {platform.release()}",
        'python_version': platform.python_version(),
        'django_version': '3.2.16',  # Update this with your Django version
        'timezone': str(timezone.get_current_timezone()),
    }
    
    # Get maintenance-related statistics
    maintenance_stats = {
        'last_backup': None,  # You would get this from your backup model
        'last_optimization': None,  # You would get this from your audit logs
        'pending_updates': False,  # You would determine this from your update check
    }
    
    # Get recent maintenance activities from audit log
    recent_activities = AuditLog.objects.filter(
        action__in=['backup_database', 'optimize_database', 'clear_cache', 'check_for_updates']
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': 'Maintenance Management',
        'active_tab': 'maintenance',
        'system_info': system_info,
        'maintenance_stats': maintenance_stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'custom_admin/maintenance_management.html', context)


def system_status(request):
    """System status dashboard"""
    # Get system information
    system_info = {
        'os': f"{platform.system()} {platform.release()}",
        'python_version': platform.python_version(),
        'django_version': '3.2.16',  # Update this with your Django version
        'database': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'timezone': str(timezone.get_current_timezone()),
        'debug': settings.DEBUG,
    }
    
    # Get system resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get recent logs
    recent_logs = AuditLog.objects.all().order_by('-timestamp')[:10]
    
    # Get active users
    active_users = []
    for user in psutil.users():
        active_users.append({
            'name': user.name,
            'terminal': user.terminal or 'N/A',
            'host': user.host or 'localhost',
            'started': datetime.fromtimestamp(user.started).strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    # Get background jobs status
    background_jobs = {
        'celery': is_process_running('celery'),
        'redis': is_process_running('redis'),
        'nginx': is_process_running('nginx'),
    }
    
    context = {
        'system_info': system_info,
        'cpu_percent': cpu_percent,
        'memory': {
            'total': memory.total / (1024 ** 3),  # Convert to GB
            'available': memory.available / (1024 ** 3),
            'percent': memory.percent,
            'used': memory.used / (1024 ** 3),
        },
        'disk': {
            'total': disk.total / (1024 ** 3),  # Convert to GB
            'used': disk.used / (1024 ** 3),
            'free': disk.free / (1024 ** 3),
            'percent': disk.percent,
        },
        'recent_logs': recent_logs,
        'active_users': active_users,
        'background_jobs': background_jobs,
        'active_tab': 'system_status',
    }
    
    return render(request, 'custom_admin/system/status.html', context)

def is_process_running(process_name):
    """Check if a process is running"""
    try:
        for proc in psutil.process_iter(['name']):
            if process_name.lower() in proc.info['name'].lower():
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

@login_required
@user_passes_test(is_admin)
def system_settings(request):
    """System settings management"""
    settings_list = SystemSetting.objects.all()
    
    if request.method == 'POST':
        form = SystemSettingForm(request.POST)
        if form.is_valid():
            setting = form.save(commit=False)
            setting.updated_by = request.user
            setting.save()
            messages.success(request, 'Setting saved successfully.')
            return redirect('custom_admin:system_settings')
    else:
        form = SystemSettingForm()
    
    return render(request, 'custom_admin/system/settings.html', {
        'settings': settings_list,
        'form': form,
        'active_tab': 'system_settings',
    })

@login_required
@user_passes_test(is_admin)
def clear_cache(request):
    """Clear system cache"""
    try:
        from django.core.cache import cache
        cache.clear()
        messages.success(request, 'Cache cleared successfully.')
    except Exception as e:
        messages.error(request, f'Error clearing cache: {str(e)}')
    
    return redirect('custom_admin:system_status')

@login_required
@user_passes_test(is_admin)
def download_logs(request):
    """Download system logs"""
    try:
        # This is a placeholder - implement actual log file handling
        response = HttpResponse("Log file content would go here", content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=system_logs.txt'
        return response
    except Exception as e:
        messages.error(request, f'Error downloading logs: {str(e)}')
        return redirect('custom_admin:system_status')

@login_required
@user_passes_test(is_admin)
def backup_database(request):
    """
    Create a database backup
    """
    try:
        from django.core.management import call_command
        from django.conf import settings
        import os
        from django.utils import timezone
        
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        db_name = settings.DATABASES['default']['NAME'].split('/')[-1]
        backup_file = os.path.join(backup_dir, f'db_backup_{db_name}_{timestamp}.json')
        
        # Create the backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', format='json', indent=2, stdout=f)
        
        # Log the backup action
        AuditLog.objects.create(
            user=request.user,
            action='BACKUP_CREATE',
            details=f'Database backup created: {os.path.basename(backup_file)}',
            status='SUCCESS'
        )
        
        # Return success response
        return JsonResponse({
            'status': 'success',
            'message': 'Database backup created successfully',
            'backup_file': os.path.basename(backup_file)
        })
        
    except Exception as e:
        # Log the error
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='BACKUP_CREATE',
            details=f'Failed to create database backup: {str(e)}',
            status='ERROR'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create database backup: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def restore_database(request):
    """
    Restore database from a backup
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed for this endpoint'
        }, status=405)
    
    try:
        from django.core.management import call_command
        from django.conf import settings
        import os
        from django.db import transaction
        
        # Check if backup file exists
        backup_file = request.POST.get('backup_file')
        if not backup_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Backup file not specified'
            }, status=400)
        
        backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_file)
        if not os.path.exists(backup_path):
            return JsonResponse({
                'status': 'error',
                'message': 'Specified backup file does not exist'
            }, status=404)
        
        # Create a backup before restoring (safety measure)
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        safety_backup = os.path.join(backup_dir, f'pre_restore_backup_{timestamp}.json')
        
        with open(safety_backup, 'w', encoding='utf-8') as f:
            call_command('dumpdata', format='json', indent=2, stdout=f)
        
        # Perform the restore within a transaction
        try:
            with transaction.atomic():
                # Flush the database (remove all data)
                call_command('flush', '--no-input')
                
                # Load the backup data
                with open(backup_path, 'r', encoding='utf-8') as f:
                    call_command('loaddata', backup_path)
                
                # Log the restore action
                AuditLog.objects.create(
                    user=request.user,
                    action='RESTORE_DATABASE',
                    details=f'Database restored from backup: {backup_file}',
                    status='SUCCESS'
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Database restored successfully',
                    'backup_created': os.path.basename(safety_backup)
                })
                
        except Exception as e:
            # If anything goes wrong, the transaction will be rolled back automatically
            error_msg = f'Failed to restore database: {str(e)}. The database has not been modified.'
            
            # Log the error
            AuditLog.objects.create(
                user=request.user,
                action='RESTORE_DATABASE',
                details=error_msg,
                status='ERROR'
            )
            
            return JsonResponse({
                'status': 'error',
                'message': error_msg
            }, status=500)
            
    except Exception as e:
        # Log the error
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='RESTORE_DATABASE',
            details=f'Failed to restore database: {str(e)}',
            status='ERROR'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin)
def optimize_database(request):
    """
    Optimize database tables to improve performance
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    start_time = time.time()
    
    try:
        # Get database engine
        engine = settings.DATABASES['default']['ENGINE']
        
        with connection.cursor() as cursor:
            if 'sqlite3' in engine:
                # SQLite optimization
                cursor.execute('VACUUM;')
                cursor.execute('ANALYZE;')
                message = "SQLite database optimized (VACUUM and ANALYZE)"
                
            elif 'postgresql' in engine:
                # PostgreSQL optimization
                cursor.execute('VACUUM ANALYZE;')
                cursor.execute('REINDEX DATABASE %s;', [settings.DATABASES['default']['NAME']])
                message = "PostgreSQL database optimized (VACUUM ANALYZE and REINDEX)"
                
            elif 'mysql' in engine or 'mariadb' in engine:
                # MySQL/MariaDB optimization
                cursor.execute('ANALYZE TABLE %s;', [', '.join(
                    table.name for table in connection.introspection.table_names(cursor)
                )])
                cursor.execute('OPTIMIZE TABLE %s;', [', '.join(
                    table.name for table in connection.introspection.table_names(cursor)
                )])
                message = "MySQL/MariaDB database optimized (ANALYZE and OPTIMIZE)"
                
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Database engine {engine} not supported for optimization'
                }, status=400)
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='optimize_database',
            target_type='system',
            target_id=0,
            target_repr='Database Optimization',
            details=f'Database optimization completed by {request.user.username}'
        )
        
        execution_time = round(time.time() - start_time, 2)
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'execution_time': f'{execution_time} seconds'
        })
        
    except Exception as e:
        # Log the error
        AuditLog.objects.create(
            user=request.user,
            action='optimize_database_error',
            target_type='system',
            target_id=0,
            target_repr='Database Optimization',
            details=f'Error during database optimization: {str(e)}',
            error=True
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Error optimizing database: {str(e)}'
        }, status=500)


@login_required
@user_passes_test(is_admin)
def check_for_updates(request):
    """
    Check for available system updates
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    try:
        # Get current version from settings
        current_version = getattr(settings, 'VERSION', '1.0.0')
        
        # In a real application, you would check against a remote API or repository
        # For demonstration, we'll simulate a check
        updates_available = False
        latest_version = current_version
        update_details = {
            'security': [],
            'features': [],
            'bugfixes': []
        }
        
        # Simulate update check (replace with actual implementation)
        # Example response structure
        # response = requests.get('https://api.your-update-server.com/check-update', 
        #                       params={'version': current_version})
        # update_data = response.json()
        
        # For demo purposes, we'll simulate an available update
        if current_version == '1.0.0':
            latest_version = '1.1.0'
            updates_available = True
            update_details = {
                'security': [
                    'Fixed critical security vulnerability in authentication',
                    'Updated dependencies with known security issues'
                ],
                'features': [
                    'Added new reporting dashboard',
                    'Improved user management interface'
                ],
                'bugfixes': [
                    'Fixed issue with data export functionality',
                    'Resolved performance problems in search feature'
                ]
            }
        
        # Log the update check
        AuditLog.objects.create(
            user=request.user,
            action='check_for_updates',
            target_type='system',
            target_id=0,
            target_repr='System Update Check',
            details=f'System update check completed. Current: {current_version}, Latest: {latest_version}'
        )
        
        return JsonResponse({
            'status': 'success',
            'current_version': current_version,
            'latest_version': latest_version,
            'updates_available': updates_available,
            'update_details': update_details,
            'last_checked': timezone.now().isoformat()
        })
        
    except Exception as e:
        # Log the error
        AuditLog.objects.create(
            user=request.user,
            action='check_for_updates_error',
            target_type='system',
            target_id=0,
            target_repr='System Update Check',
            details=f'Error checking for updates: {str(e)}',
            error=True
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Error checking for updates: {str(e)}'
        }, status=500)
