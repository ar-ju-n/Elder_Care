from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import UserProfileForm, UserSettingsForm, CustomAuthenticationForm, CustomUserCreationForm
from .services import login_user
from .models import AccountDeletionRequest
from django.utils import timezone
from datetime import timedelta

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

def login_view(request):
    # Redirect already logged-in users
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('landing')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = login_user(request, username, password)
        if user:
            messages.success(request, f"Welcome back, {user.username}!")
            # Redirect to the next parameter if it exists, otherwise to landing
            next_url = request.GET.get('next', 'landing')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html', {'form': CustomAuthenticationForm()})

def logout_view(request):
    logout(request)
    return render(request, 'accounts/logout.html')

from .forms import CaregiverVerificationForm
from .models import CaregiverVerification

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Ensure no one can register as admin through form manipulation
            if user.role == 'admin':
                user.role = 'elderly'  # Default to elderly if someone tries to hack the form
            user.save()
            # If caregiver, create blank verification record
            if user.role == 'caregiver':
                CaregiverVerification.objects.get_or_create(user=user)
            # Log the user in
            login(request, user)
            # Redirect to profile completion
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """View for user profile"""
    user = request.user
    caregiver_verification = None
    verification_form = None
    verification_status = None
    CaregiverVerificationModel = None
    try:
        from .models import CaregiverVerification
        CaregiverVerificationModel = CaregiverVerification
    except ImportError:
        pass
    if user.is_caregiver() and CaregiverVerificationModel:
        caregiver_verification, _ = CaregiverVerificationModel.objects.get_or_create(user=user)
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES, instance=user)
            verification_form = CaregiverVerificationForm(request.POST, request.FILES, instance=caregiver_verification)
            valid_profile = form.is_valid()
            valid_verification = verification_form.is_valid()
            if valid_profile and valid_verification:
                form.save()
                verification_form.save()
                messages.success(request, 'Your profile and verification info have been updated.')
                return redirect('accounts:profile')
            else:
                if not valid_profile:
                    print(f"Profile form errors: {form.errors}")
                if not valid_verification:
                    print(f"Verification form errors: {verification_form.errors}")
        else:
            form = UserProfileForm(instance=user)
            verification_form = CaregiverVerificationForm(instance=caregiver_verification)
        verification_status = {
            'reviewed': caregiver_verification.reviewed,
            'approved': caregiver_verification.approved,
            'admin_comment': caregiver_verification.admin_comment,
        }
    else:
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
            else:
                print(f"Form errors: {form.errors}")
        else:
            form = UserProfileForm(instance=user)
    if user.profile_picture:
        print(f"Existing profile picture: {user.profile_picture.name}")
        print(f"Existing profile picture URL: {user.profile_picture.url}")
    pending_deletion = user.is_pending_deletion
    scheduled_deletion_at = user.scheduled_deletion_at
    context = {
        'form': form,
        'pending_deletion': pending_deletion,
        'scheduled_deletion_at': scheduled_deletion_at
    }
    if user.is_caregiver() and CaregiverVerificationModel:
        context['verification_form'] = verification_form
        context['verification_status'] = verification_status
    return render(request, 'accounts/profile.html', context)


@login_required
def settings_view(request):
    """
    User settings page for account preferences
    """
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated successfully.')
            return redirect('accounts:settings')
    else:
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'accounts/settings.html', {
        'form': form,
    })

def auth_status(request):
    """Debug view to check authentication status"""
    context = {
        'is_authenticated': request.user.is_authenticated,
        'user': request.user,
        'session_data': dict(request.session),
    }
    return render(request, 'accounts/auth_status.html', context)

@login_required
def request_account_deletion(request):
    if request.method == "POST":
        # Prevent duplicate requests
        if not AccountDeletionRequest.objects.filter(user=request.user, approved=False).exists():
            AccountDeletionRequest.objects.create(user=request.user)
        messages.info(request, "Your account deletion request has been submitted and is pending admin approval.")
        return redirect('accounts:profile')
    return redirect('accounts:profile')

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.is_pending_deletion = True
        user.scheduled_deletion_at = timezone.now() + timedelta(days=3)
        user.save()
        logout(request)
        messages.success(request, "Your account is scheduled for deletion in 3 days. If you change your mind, contact support before then.")
        return redirect('landing')
    return render(request, "accounts/confirm_delete_account.html")

@login_required
def cancel_account_deletion(request):
    if request.method == "POST":
        user = request.user
        if user.is_pending_deletion:
            user.is_pending_deletion = False
            user.scheduled_deletion_at = None
            user.is_active = True
            user.save()
            messages.success(request, "Your account deletion has been cancelled.")
        return redirect('accounts:profile')
    return redirect('accounts:profile')
