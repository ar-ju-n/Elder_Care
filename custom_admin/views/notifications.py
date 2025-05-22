"""
Notification Management Views for Custom Admin
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from core.models import Notification, NotificationTemplate, AuditLog
from accounts.models import User

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def notification_list(request):
    """
    List all notifications in the system
    """
    # Get query parameters
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Start with base queryset
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Apply filters
    if status != 'all':
        notifications = notifications.filter(status=status.upper())
    
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search) |
            Q(recipient__username__icontains=search) |
            Q(recipient__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(notifications, 25)  # 25 items per page
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'status_filter': status,
        'search_query': search,
        'status_choices': dict(Notification.STATUS_CHOICES),
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/notification_list.html', context)

@login_required
@user_passes_test(is_admin)
def notification_management(request):
    """
    Main notification management entry point. For now, just show the notification list.
    """
    return notification_list(request)

@login_required
@user_passes_test(is_admin)
def notification_detail(request, notification_id):
    """
    View details of a specific notification
    """
    notification = get_object_or_404(Notification, id=notification_id)
    
    # Mark as read if it's unread
    if notification.status == 'UNREAD':
        notification.status = 'READ'
        notification.save()
    
    context = {
        'notification': notification,
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/notification_detail.html', context)

@login_required
@user_passes_test(is_admin)
def notification_create(request):
    """
    Create a new notification
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_id = request.POST.get('recipient')
        notification_type = request.POST.get('notification_type', 'INFO')
        
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Create the notification
            notification = Notification.objects.create(
                title=title,
                message=message,
                recipient=recipient,
                notification_type=notification_type,
                created_by=request.user
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='NOTIFICATION_CREATE',
                details=f'Created notification for {recipient.username}',
                status='SUCCESS'
            )
            
            messages.success(request, 'Notification sent successfully.')
            return redirect('custom_admin:notification_list')
            
        except User.DoesNotExist:
            messages.error(request, 'Recipient not found.')
        except Exception as e:
            messages.error(request, f'Error creating notification: {str(e)}')
    
    # Get all active users for the recipient dropdown
    recipients = User.objects.filter(is_active=True)
    
    context = {
        'recipients': recipients,
        'notification_types': dict(Notification.NOTIFICATION_TYPES),
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/notification_form.html', context)

@login_required
@user_passes_test(is_admin)
def notification_mark_read(request, notification_id):
    """
    Mark a notification as read
    """
    notification = get_object_or_404(Notification, id=notification_id)
    
    if notification.status != 'READ':
        notification.status = 'READ'
        notification.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='NOTIFICATION_READ',
            details=f'Marked notification #{notification.id} as read',
            status='SUCCESS'
        )
    
    if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('custom_admin:notification_detail', notification_id=notification.id)

@login_required
@user_passes_test(is_admin)
def notification_delete(request, notification_id):
    """
    Delete a notification
    """
    notification = get_object_or_404(Notification, id=notification_id)
    
    if request.method == 'POST':
        try:
            # Log the action before deletion
            AuditLog.objects.create(
                user=request.user,
                action='NOTIFICATION_DELETE',
                details=f'Deleted notification #{notification.id}',
                status='SUCCESS'
            )
            
            notification.delete()
            messages.success(request, 'Notification deleted successfully.')
            return redirect('custom_admin:notification_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting notification: {str(e)}')
            return redirect('custom_admin:notification_detail', notification_id=notification.id)
    
    context = {
        'notification': notification,
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/notification_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def notification_templates(request):
    """
    List all notification templates
    """
    templates = NotificationTemplate.objects.all().order_by('name')
    
    context = {
        'templates': templates,
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/template_list.html', context)

@login_required
@user_passes_test(is_admin)
def notification_template_edit(request, template_id=None):
    """
    Create or edit a notification template
    """
    if template_id:
        template = get_object_or_404(NotificationTemplate, id=template_id)
        is_edit = True
    else:
        template = None
        is_edit = False
    
    if request.method == 'POST':
        name = request.POST.get('name')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        notification_type = request.POST.get('notification_type', 'SYSTEM')
        
        try:
            if is_edit:
                template.name = name
                template.subject = subject
                template.body = body
                template.notification_type = notification_type
                template.save()
                
                action = 'updated'
            else:
                template = NotificationTemplate.objects.create(
                    name=name,
                    subject=subject,
                    body=body,
                    notification_type=notification_type,
                    created_by=request.user
                )
                action = 'created'
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='TEMPLATE_UPDATE' if is_edit else 'TEMPLATE_CREATE',
                details=f'Template "{template.name}" {action}',
                status='SUCCESS'
            )
            
            messages.success(request, f'Template {action} successfully.')
            return redirect('custom_admin:notification_templates')
            
        except Exception as e:
            messages.error(request, f'Error saving template: {str(e)}')
    
    context = {
        'template': template,
        'is_edit': is_edit,
        'notification_types': dict(NotificationTemplate.NOTIFICATION_TYPES),
        'active_tab': 'notifications',
    }
    
    return render(request, 'custom_admin/notifications/template_form.html', context)
