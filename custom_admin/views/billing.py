"""
Placeholder view for Billing Controls in Custom Admin
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def billing_controls(request):
    """Placeholder page for billing controls"""
    return render(request, 'custom_admin/billing/coming_soon.html')
