
"""
User Management Views for Custom Admin
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
import csv

from accounts.models import CaregiverVerification
from custom_admin.mixins import AdminRequiredMixin

User = get_user_model()

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def user_management(request):
    """User management dashboard"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'custom_admin/users/user_management.html', {
        'users': users,
        'active_tab': 'users'
    })

@login_required
@user_passes_test(is_admin)
def user_roles_edit(request, user_id):
    """Edit user roles and permissions"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        # Update basic fields
        user.is_active = is_active
        
        # Update role
        if role in ['admin', 'caregiver', 'family']:
            user.role = role
            
            # Update staff status based on role
            user.is_staff = (role == 'admin')
            user.save()
            
            messages.success(request, f'User {user.get_full_name()} updated successfully.')
            return redirect('custom_admin:user_management')
    
    return render(request, 'custom_admin/users/user_roles_edit.html', {
        'user': user,
        'roles': User.ROLE_CHOICES
    })

@login_required
@user_passes_test(is_admin)
def caregiver_verification_list(request):
    """List caregiver verification requests"""
    verifications = CaregiverVerification.objects.all().order_by('-submitted_at')
    return render(request, 'custom_admin/users/caregiver_verification_list.html', {
        'verifications': verifications,
        'active_tab': 'caregiver_verifications'
    })

@login_required
@user_passes_test(is_admin)
def caregiver_verification_review(request, verification_id):
    verification = get_object_or_404(CaregiverVerification, id=verification_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_comment = request.POST.get('admin_comment', '')
        verification.reviewed = True
        verification.reviewed_at = timezone.now()
        verification.admin_comment = admin_comment
        if action == 'approve':
            verification.approved = True
            messages.success(request, 'Caregiver verification approved.')
        elif action == 'reject':
            verification.approved = False
            messages.success(request, 'Caregiver verification rejected.')
        verification.save()
        return redirect('custom_admin:users:caregiver_verification_list')
    return render(request, 'custom_admin/users/caregiver_verification_review.html', {
        'verification': verification
    })

    """List caregiver verification requests"""
    verifications = CaregiverVerification.objects.all().order_by('-submitted_at')
    return render(request, 'custom_admin/users/caregiver_verification_list.html', {
        'verifications': verifications,
        'active_tab': 'caregiver_verifications'
    })

@login_required
@user_passes_test(is_admin)
def update_application_status(request, application_id, status):
    """Update caregiver application status"""
    application = get_object_or_404(CaregiverVerification, id=application_id)
    
    if status in ['pending', 'approved', 'rejected']:
        application.status = status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        # Update user role if approved
        if status == 'approved':
            application.user.role = 'caregiver'
            application.user.save()
        
        messages.success(request, f'Application {status} successfully.')
    
    return redirect('custom_admin:users:caregiver_verification_list')

@login_required
@user_passes_test(is_admin)
def export_users(request):
    """Export users to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Email', 'First Name', 'Last Name', 'Role', 'Date Joined', 'Last Login'])
    
    users = User.objects.all().values_list('id', 'email', 'first_name', 'last_name', 'role', 'date_joined', 'last_login')
    for user in users:
        writer.writerow(user)
    
    return response

@login_required
@user_passes_test(is_admin)
def user_import(request):
    """Import users from CSV"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('custom_admin:user_management')
        
        try:
            import csv
            from django.contrib.auth.hashers import make_password
            
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            for row in reader:
                user, created = User.objects.get_or_create(
                    email=row['email'],
                    defaults={
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'role': row.get('role', 'family'),
                        'is_active': row.get('is_active', 'true').lower() == 'true',
                        'password': make_password(row.get('password', 'defaultpassword123')),
                    }
                )
                
                if not created:
                    # Update existing user
                    user.first_name = row.get('first_name', user.first_name)
                    user.last_name = row.get('last_name', user.last_name)
                    user.role = row.get('role', user.role)
                    user.is_active = row.get('is_active', 'true').lower() == 'true'
                    if 'password' in row:
                        user.set_password(row['password'])
                    user.save()
            
            messages.success(request, 'Users imported successfully.')
            
        except Exception as e:
            messages.error(request, f'Error importing users: {str(e)}')
    
    return redirect('custom_admin:user_management')
