"""
Placeholder view for Communication Oversight in Custom Admin
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def communication_oversight(request):
    """Placeholder page for communication oversight"""
    return render(request, 'custom_admin/communication/coming_soon.html')
