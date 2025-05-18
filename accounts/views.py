from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import UserProfileForm, UserSettingsForm, CustomAuthenticationForm, CustomUserCreationForm
from .services import login_user
from .models import AccountDeletionRequest, EmergencyContact
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification, User
from django.http import JsonResponse

# AJAX endpoints for live username/email validation

def check_username(request):
    username = request.GET.get('username', '').strip()
    available = False
    if username and len(username) >= 3:
        # For login: available=False means user exists, available=True means user does not exist
        from .models import User
        available = not User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': available})

def check_email(request):
    email = request.GET.get('email', '').strip()
    available = False
    if email:
        from .models import User
        available = not User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'available': available})

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

from .forms import CaregiverVerificationForm, EmergencyContactForm, CustomUserCreationForm
from .models import CaregiverVerification


def family_register_view(request):
    # Single-step registration for family members
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'family'
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            # Notify admins (email + in-app notification)
            admin_qs = User.objects.filter(is_staff=True)
            admin_emails = list(admin_qs.values_list('email', flat=True))
            if admin_emails:
                admin_html = render_to_string('emails/admin_new_family.html', {'user': user})
                send_mail(
                    subject='New Family Member Registration',
                    message=f'A new family member has registered: {user.full_name} ({user.email})',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                    html_message=admin_html,
                )
                # In-app notification for each admin
                for admin in admin_qs:
                    Notification.objects.create(
                        recipient=admin,
                        message=f'New family member registered: {user.full_name} ({user.email})',
                        url=f'/accounts/profile/{user.id}/'
                    )
            # Welcome email to user (HTML)
            welcome_html = render_to_string('emails/welcome_family.html', {'user': user})
            send_mail(
                subject='Welcome to Elder Care Hub',
                message=f'Dear {user.full_name},\n\nWelcome to Elder Care Hub! Your account has been successfully created as a family member.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
                html_message=welcome_html,
            )
            return redirect('accounts:profile', user_id=user.id)
    else:
        form = CustomUserCreationForm(initial={'role': 'family'})
    return render(request, 'accounts/register_family.html', {'form': form})

def caregiver_register_view(request):
    # Multi-step registration for caregivers
    if request.method == 'POST':
        step = request.POST.get('step', '1')
        if step == '1':
            user_form = CustomUserCreationForm(request.POST)
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.role = 'caregiver'
                user.is_active = False  # Optionally require admin verification before login
                user.save()
                request.session['pending_caregiver_id'] = user.id
                return render(request, 'accounts/register_caregiver_step2.html', {
                    'verification_form': CaregiverVerificationForm(),
                    'step': '2',
                })
            else:
                return render(request, 'accounts/register_caregiver_step1.html', {
                    'user_form': user_form,
                    'step': '1',
                })
        elif step == '2':
            caregiver_id = request.session.get('pending_caregiver_id')
            user = get_object_or_404(User, id=caregiver_id)
            verification_form = CaregiverVerificationForm(request.POST, request.FILES)
            if verification_form.is_valid():
                verification = verification_form.save(commit=False)
                verification.user = user
                verification.save()
                user.is_active = True  # Optionally activate after document upload
                user.save()
                # Notify admins (email + in-app notification)
                admin_qs = User.objects.filter(is_staff=True)
                admin_emails = list(admin_qs.values_list('email', flat=True))
                if admin_emails:
                    admin_html = render_to_string('emails/admin_new_caregiver.html', {'user': user})
                    send_mail(
                        subject='New Caregiver Registration',
                        message=f'A new caregiver has registered: {user.full_name} ({user.email}). Please review their submitted documents for verification.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=True,
                        html_message=admin_html,
                    )
                    # In-app notification for each admin
                    for admin in admin_qs:
                        Notification.objects.create(
                            recipient=admin,
                            message=f'New caregiver registered: {user.full_name} ({user.email}). Please review their documents.',
                            url=f'/accounts/profile/{user.id}/'
                        )
                # Welcome email to user (HTML)
                welcome_html = render_to_string('emails/welcome_caregiver.html', {'user': user})
                send_mail(
                    subject='Welcome to Elder Care Hub',
                    message=f'Dear {user.full_name},\n\nWelcome to Elder Care Hub! Your caregiver account has been created. Your documents have been submitted for admin review. You will be notified once verified.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                    html_message=welcome_html,
                )
                login(request, user)
                del request.session['pending_caregiver_id']
                messages.success(request, 'Registration successful! Your documents will be reviewed by admin.')
                return redirect('accounts:profile', user_id=user.id)
            else:
                return render(request, 'accounts/register_caregiver_step2.html', {
                    'verification_form': verification_form,
                    'step': '2',
                })
    else:
        # GET request, start at step 1
        user_form = CustomUserCreationForm(initial={'role': 'caregiver'})
        return render(request, 'accounts/register_caregiver_step1.html', {
            'user_form': user_form,
            'step': '1',
        })

@login_required
def emergency_contacts_view(request):
    contacts = EmergencyContact.objects.filter(user=request.user)
    form = EmergencyContactForm()
    edit_form = None
    edit_id = request.GET.get('edit')
    if edit_id:
        contact = EmergencyContact.objects.get(id=edit_id, user=request.user)
        edit_form = EmergencyContactForm(instance=contact)
    if request.method == 'POST':
        if 'add_contact' in request.POST:
            form = EmergencyContactForm(request.POST)
            if form.is_valid():
                new_contact = form.save(commit=False)
                new_contact.user = request.user
                if new_contact.is_primary:
                    EmergencyContact.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
                new_contact.save()
                messages.success(request, 'Emergency contact added.')
                return redirect('accounts:emergency_contacts')
        elif 'edit_contact' in request.POST:
            contact = EmergencyContact.objects.get(id=request.POST.get('edit_id'), user=request.user)
            edit_form = EmergencyContactForm(request.POST, instance=contact)
            if edit_form.is_valid():
                updated = edit_form.save(commit=False)
                if updated.is_primary:
                    EmergencyContact.objects.filter(user=request.user, is_primary=True).exclude(id=updated.id).update(is_primary=False)
                updated.save()
                messages.success(request, 'Emergency contact updated.')
                return redirect('accounts:emergency_contacts')
        elif 'delete_contact' in request.POST:
            contact = EmergencyContact.objects.get(id=request.POST.get('delete_id'), user=request.user)
            contact.delete()
            messages.success(request, 'Emergency contact deleted.')
            return redirect('accounts:emergency_contacts')
    return render(request, 'accounts/emergency_contacts.html', {
        'contacts': contacts,
        'form': form,
        'edit_form': edit_form,
        'edit_id': edit_id,
    })

@login_required
def medication_reminders_view(request):
    reminders = request.user.medication_reminders.all()
    form = MedicationReminderForm()
    edit_form = None
    edit_id = request.GET.get('edit')
    if edit_id:
        reminder = request.user.medication_reminders.get(id=edit_id)
        edit_form = MedicationReminderForm(instance=reminder)
    if request.method == 'POST':
        if 'add_reminder' in request.POST:
            form = MedicationReminderForm(request.POST)
            if form.is_valid():
                new_reminder = form.save(commit=False)
                new_reminder.user = request.user
                new_reminder.save()
                messages.success(request, 'Medication reminder added.')
                return redirect('accounts:medication_reminders')
        elif 'edit_reminder' in request.POST:
            reminder = request.user.medication_reminders.get(id=request.POST.get('edit_id'))
            edit_form = MedicationReminderForm(request.POST, instance=reminder)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Medication reminder updated.')
                return redirect('accounts:medication_reminders')
        elif 'delete_reminder' in request.POST:
            reminder = request.user.medication_reminders.get(id=request.POST.get('delete_id'))
            reminder.delete()
            messages.success(request, 'Medication reminder deleted.')
            return redirect('accounts:medication_reminders')
    return render(request, 'accounts/medication_reminders.html', {
        'reminders': reminders,
        'form': form,
        'edit_form': edit_form,
        'edit_id': edit_id,
    })

@login_required
def profile_view(request, user_id):
    """View for user profile"""
    from .models import User
    user = get_object_or_404(User, id=user_id)
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
                return redirect('accounts:profile', user_id=user.id)
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
                return redirect('accounts:profile', user_id=user.id)
            else:
                print(f"Form errors: {form.errors}")
        else:
            form = UserProfileForm(instance=user)
    if user.profile_picture:
        print(f"Existing profile picture: {user.profile_picture.name}")
        print(f"Existing profile picture URL: {user.profile_picture.url}")
    pending_deletion = user.is_pending_deletion
    scheduled_deletion_at = user.scheduled_deletion_at
    from events.models import Event
    attending_events = user.events_attending.order_by('start_time')
    from forum.models import Topic, Reply
    recent_forum_topics = user.forum_topics.order_by('-created_at')[:5]
    recent_forum_replies = user.forum_replies.order_by('-created_at')[:5]
    # Handle forum email notification preference update
    profile = getattr(user, 'profile', None)
    if request.method == 'POST' and 'forum_email_notifications' in request.POST:
        if profile:
            profile.forum_email_notifications = bool(request.POST.get('forum_email_notifications'))
            profile.save()
    forum_email_notifications = profile.forum_email_notifications if profile else True
    # --- Badges ---
    badges = []
    if hasattr(user, 'is_verified_caregiver') and user.is_verified_caregiver():
        badges.append({
            'label': 'Verified Caregiver',
            'icon': 'bi-patch-check-fill',
            'color': 'success',
            'url': '',
            'tooltip': 'This user is a verified caregiver.'
        })
    if hasattr(user, 'is_admin_role') and user.is_admin_role():
        badges.append({
            'label': 'Admin',
            'icon': 'bi-shield-lock-fill',
            'color': 'danger',
            'url': '',
            'tooltip': 'This user is an administrator.'
        })
    # Achievements
    topic_count = user.forum_topics.count() if hasattr(user, 'forum_topics') else 0
    reply_count = user.forum_replies.count() if hasattr(user, 'forum_replies') else 0
    # Upvotes and best answers (if available)
    upvotes = getattr(user, 'upvotes_received', 0)
    best_answers = getattr(user, 'best_answers', 0)
    # Top Helper (most replies)
    if reply_count >= 50:
        badges.append({
            'label': 'Top Helper',
            'icon': 'bi-people-fill',
            'color': 'info',
            'url': f"/forum/user/{user.id}/replies/",
            'tooltip': 'This user has provided many helpful replies.'
        })
    # Most Upvoted (if upvotes available)
    if upvotes >= 10:
        badges.append({
            'label': 'Most Upvoted',
            'icon': 'bi-hand-thumbs-up-fill',
            'color': 'primary',
            'url': f"/forum/user/{user.id}/topics/",
            'tooltip': 'This user has received many upvotes.'
        })
    # Best Answer (if available)
    if best_answers >= 1:
        badges.append({
            'label': 'Best Answer',
            'icon': 'bi-award-fill',
            'color': 'success',
            'url': f"/forum/user/{user.id}/replies/",
            'tooltip': 'This user has replies marked as best answers.'
        })
    if topic_count >= 1:
        badges.append({
            'label': 'First Topic',
            'icon': 'bi-star-fill',
            'color': 'warning',
            'url': f"/forum/user/{user.id}/topics/",
            'tooltip': 'Started their first topic.'
        })
    if topic_count >= 10:
        badges.append({
            'label': '10 Topics',
            'icon': 'bi-trophy-fill',
            'color': 'primary',
            'url': f"/forum/user/{user.id}/topics/",
            'tooltip': 'Started 10 topics.'
        })
    if reply_count >= 10:
        badges.append({
            'label': '10 Replies',
            'icon': 'bi-chat-dots-fill',
            'color': 'info',
            'url': f"/forum/user/{user.id}/replies/",
            'tooltip': 'Posted 10 replies.'
        })
    if reply_count >= 100:
        badges.append({
            'label': '100 Replies',
            'icon': 'bi-fire',
            'color': 'danger',
            'url': f"/forum/user/{user.id}/replies/",
            'tooltip': 'Posted 100 replies.'
        })
    # --- Activity Stats ---
    activity_stats = {
        'topics': topic_count,
        'replies': reply_count,
        'upvotes': upvotes,
        'best_answers': best_answers,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    context = {
        'form': form,
        'pending_deletion': pending_deletion,
        'scheduled_deletion_at': scheduled_deletion_at,
        'attending_events': attending_events,
        'recent_forum_topics': recent_forum_topics,
        'recent_forum_replies': recent_forum_replies,
        'forum_email_notifications': forum_email_notifications,
        'badges': badges,
        'activity_stats': activity_stats,
        'profile_user': user,
    }
    if user.is_caregiver() and CaregiverVerificationModel:
        context['verification_form'] = verification_form
        context['verification_status'] = verification_status

    is_owner = request.user.id == user.id
    is_admin = request.user.is_staff or request.user.is_superuser
    # Restrict access to unverified caregiver profiles
    if user.is_caregiver() and not user.is_verified and not (is_owner or is_admin):
        messages.error(request, "This caregiver is not yet verified and cannot be viewed.")
        return redirect('landing')
    if user.profile_visibility == user.PRIVATE and not (is_owner or is_admin):
        return render(request, 'accounts/profile_private.html', {'profile_user': user})
    # Add emergency_contacts for modal in base.html
    if request.user.is_authenticated:
        emergency_contacts = list(request.user.emergency_contacts.all())
        print(f"[DEBUG] User {request.user.username} emergency contacts: {emergency_contacts}")
        context['emergency_contacts'] = emergency_contacts
    else:
        print("[DEBUG] No authenticated user; emergency_contacts empty.")
        context['emergency_contacts'] = []
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
    
    # Add emergency_contacts for modal in base.html
    emergency_contacts = request.user.emergency_contacts.all() if request.user.is_authenticated else []
    return render(request, 'accounts/settings.html', {
        'form': form,
        'emergency_contacts': emergency_contacts,
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
        return redirect('accounts:profile', user_id=user.id)
    return redirect('accounts:profile', user_id=user.id)

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
        return redirect('accounts:profile', user_id=user.id)
    return redirect('accounts:profile', user_id=user.id)
