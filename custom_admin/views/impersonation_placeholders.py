from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def impersonate_user(request, user_id=None):
    return HttpResponse("Impersonate User - Coming Soon")

@login_required
@user_passes_test(is_admin)
def stop_impersonation(request):
    return HttpResponse("Stop Impersonation - Coming Soon")
