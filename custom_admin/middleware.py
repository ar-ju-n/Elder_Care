from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from custom_admin.models import AuditLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(user=user, action='User Login', details=f'IP: {get_client_ip(request)}')
    request.session['login_time'] = timezone.now().isoformat()

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    login_time = request.session.get('login_time')
    logout_time = timezone.now()
    session_duration = None
    if login_time:
        try:
            login_dt = timezone.datetime.fromisoformat(login_time)
            session_duration = (logout_time - login_dt).total_seconds()
        except Exception:
            pass
    AuditLog.objects.create(
        user=user,
        action='User Logout',
        details=f'IP: {get_client_ip(request)}; Session duration: {session_duration or "unknown"} seconds'
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
