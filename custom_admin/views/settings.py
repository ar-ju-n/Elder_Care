"""
Settings Management Views for Custom Admin
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods

from core.models import SystemSetting, AuditLog
from core.forms import GeneralSettingsForm, EmailSettingsForm, SecuritySettingsForm

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def general_settings(request):
    """
    General system settings
    """
    if request.method == 'POST':
        form = GeneralSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            # Save settings to database
            for field, value in form.cleaned_data.items():
                SystemSetting.objects.update_or_create(
                    key=f'GENERAL_{field.upper()}',
                    defaults={'value': value}
                )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='SETTINGS_UPDATE',
                details='Updated general settings',
                status='SUCCESS'
            )
            
            messages.success(request, 'General settings updated successfully.')
            return redirect('custom_admin:general_settings')
    else:
        # Get current settings
        initial = {
            'site_name': getattr(settings, 'SITE_NAME', ''),
            'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
            'time_zone': getattr(settings, 'TIME_ZONE', 'UTC'),
            'date_format': getattr(settings, 'DATE_FORMAT', 'Y-m-d'),
            'time_format': getattr(settings, 'TIME_FORMAT', 'H:i'),
            'items_per_page': getattr(settings, 'ITEMS_PER_PAGE', 25),
        }
        form = GeneralSettingsForm(initial=initial)
    
    context = {
        'form': form,
        'active_tab': 'settings',
        'active_subtab': 'general',
    }
    
    return render(request, 'custom_admin/settings/general.html', context)

@login_required
@user_passes_test(is_admin)
def email_settings(request):
    """
    Email server settings
    """
    if request.method == 'POST':
        form = EmailSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            # Save settings to database
            for field, value in form.cleaned_data.items():
                SystemSetting.objects.update_or_create(
                    key=f'EMAIL_{field.upper()}',
                    defaults={'value': value}
                )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='SETTINGS_UPDATE',
                details='Updated email settings',
                status='SUCCESS'
            )
            
            messages.success(request, 'Email settings updated successfully.')
            return redirect('custom_admin:email_settings')
    else:
        # Get current settings
        initial = {
            'email_host': getattr(settings, 'EMAIL_HOST', ''),
            'email_port': getattr(settings, 'EMAIL_PORT', 587),
            'email_host_user': getattr(settings, 'EMAIL_HOST_USER', ''),
            'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
            'email_use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
            'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
            'server_email': getattr(settings, 'SERVER_EMAIL', ''),
        }
        form = EmailSettingsForm(initial=initial)
    
    context = {
        'form': form,
        'active_tab': 'settings',
        'active_subtab': 'email',
    }
    
    return render(request, 'custom_admin/settings/email.html', context)

@login_required
@user_passes_test(is_admin)
def security_settings(request):
    """
    Security-related settings
    """
    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST, instance=settings)
        if form.is_valid():
            # Save settings to database
            for field, value in form.cleaned_data.items():
                SystemSetting.objects.update_or_create(
                    key=f'SECURITY_{field.upper()}',
                    defaults={'value': value}
                )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='SETTINGS_UPDATE',
                details='Updated security settings',
                status='SUCCESS'
            )
            
            messages.success(request, 'Security settings updated successfully.')
            return redirect('custom_admin:security_settings')
    else:
        # Get current settings
        initial = {
            'password_min_length': getattr(settings, 'PASSWORD_MIN_LENGTH', 8),
            'password_require_uppercase': getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True),
            'password_require_lowercase': getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True),
            'password_require_numbers': getattr(settings, 'PASSWORD_REQUIRE_NUMBERS', True),
            'password_require_symbols': getattr(settings, 'PASSWORD_REQUIRE_SYMBOLS', True),
            'login_attempts_limit': getattr(settings, 'LOGIN_ATTEMPTS_LIMIT', 5),
            'login_timeout': getattr(settings, 'LOGIN_TIMEOUT', 900),  # 15 minutes
            'session_timeout': getattr(settings, 'SESSION_COOKIE_AGE', 1209600) // 3600,  # Convert to hours
        }
        form = SecuritySettingsForm(initial=initial)
    
    context = {
        'form': form,
        'active_tab': 'settings',
        'active_subtab': 'security',
    }
    
    return render(request, 'custom_admin/settings/security.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def test_email(request):
    """
    Send a test email to verify email settings
    """
    from django.core.mail import send_mail
    
    try:
        email = request.user.email
        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Your account does not have an email address.'
            }, status=400)
        
        send_mail(
            'Test Email from Elder Care Admin',
            'This is a test email to verify your email settings are working correctly.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='EMAIL_TEST',
            details='Sent test email',
            status='SUCCESS'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Test email sent successfully to {email}.'
        })
        
    except Exception as e:
        # Log the error
        AuditLog.objects.create(
            user=request.user,
            action='EMAIL_TEST',
            details=f'Failed to send test email: {str(e)}',
            status='ERROR'
        )
        
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to send test email: {str(e)}'
        }, status=500)
