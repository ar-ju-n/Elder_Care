import base64
import qrcode
import qrcode.image.svg
from io import BytesIO
import os
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, Http404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import pyotp
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django import forms
from .forms import ProfileForm, UserSettingsForm, CustomAuthenticationForm, CustomUserCreationForm
from .services import login_user
from .models import AccountDeletionRequest, EmergencyContact, ConnectionRequest, User, Notification
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import Notification, User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse, HttpResponse
import json
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from django.views.decorators.http import require_GET

@login_required
@require_GET
def notifications_api_recent(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    data = {
        "notifications": [
            {
                "message": n.message,
                "url": n.url,
                "created_at": n.created_at.strftime('%Y-%m-%d %H:%M'),
                "is_read": n.is_read,
            } for n in notifications
        ]
    }
    return JsonResponse(data)

@login_required
@require_GET
def messages_api_recent(request):
    from .models import Message
    messages_qs = Message.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    data = {
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "sender": m.sender.get_full_name() or m.sender.username,
                "sender_id": m.sender.id,
                "created_at": m.created_at.strftime('%Y-%m-%d %H:%M'),
                "is_read": m.is_read,
            } for m in messages_qs
        ]
    }
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def messages_api_mark_read(request):
    from .models import Message
    Message.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def send_notification(recipient, title, message, url=''):
    """
    Utility function to send a notification to a user
    """
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        url=url
    )
    
    # Send WebSocket notification if user is connected
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{recipient.id}',
            {
                'type': 'send_notification',
                'content': {
                    'type': 'new_notification',
                    'title': title,
                    'message': message,
                    'url': url,
                    'unread_count': Notification.objects.filter(
                        recipient=recipient,
                        is_read=False
                    ).count()
                }
            }
        )
    except Exception as e:
        print(f"Error sending WebSocket notification: {e}")
    
    return notification

@login_required
def notifications_list(request):
    """
    Display all notifications for the current user with pagination
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    # Get all notifications for the user, ordered by most recent
    notifications_list = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark notifications as read when viewed
    unread_notifications = notifications_list.filter(is_read=False)
    unread_count = unread_notifications.count()
    unread_notifications.update(is_read=True)
    
    # Pagination - 10 items per page
    paginator = Paginator(notifications_list, 10)
    page = request.GET.get('page')
    
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        notifications = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        notifications = paginator.page(paginator.num_pages)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'accounts/notifications_list.html', context)

@login_required
def notifications_api_mark_read(request):
    """
    Mark all notifications as read for the current user
    """
    if request.method == 'POST':
        # Mark all unread notifications as read
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'updated': updated
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

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

from .forms import (
    CaregiverVerificationForm, 
    EmergencyContactForm, 
    CustomUserCreationForm,
    ProfileForm,
    PrivacySettingsForm,
    NotificationSettingsForm
)
from .models import CaregiverVerification


def family_register_view(request):
    # Single-step registration for family members
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['role'] = 'family'
        print('POST DATA:', dict(post_data))
        form = CustomUserCreationForm(post_data)
        if not form.is_valid():
            print('FORM ERRORS:', form.errors)
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
            # Create a mutable copy of the POST data
            post_data = request.POST.copy()
            # Force the role to be 'caregiver' and ensure it's in the form data
            post_data['role'] = 'caregiver'
            if 'role' not in post_data:
                post_data['role'] = 'caregiver'
            
            user_form = CustomUserCreationForm(
                post_data,
                request.FILES
            )
            print("Form data:", post_data)  # Debug
            print("Form errors:", user_form.errors)  # Debug
            if user_form.is_valid():
                user = user_form.save(commit=False)
                user.role = 'caregiver'  # Ensure role is set
                user.save()
                
                # Store user ID in session for step 2
                request.session['pending_caregiver_id'] = user.id
                
                # Create verification form for step 2
                verification_form = CaregiverVerificationForm()
                return render(request, 'accounts/register_caregiver_step2.html', {
                    'verification_form': verification_form,
                    'step': '2',
                })
            else:
                return render(request, 'accounts/register_caregiver_step1.html', {
                    'user_form': user_form,
                    'step': '1',
                })
                
        elif step == '2':
            caregiver_id = request.session.get('pending_caregiver_id')
            if not caregiver_id:
                messages.error(request, 'Session expired. Please start registration again.')
                return redirect('accounts:register_caregiver')
                
            user = get_object_or_404(User, id=caregiver_id)
            verification_form = CaregiverVerificationForm(request.POST, request.FILES)
            
            if verification_form.is_valid():
                verification = verification_form.save(commit=False)
                verification.user = user
                verification.save()
                
                # Log the user in after successful verification
                login(request, user)
                
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
                    message=f'Dear {user.full_name}\n\nWelcome to Elder Care Hub! Your caregiver account has been created. Your documents have been submitted for admin review. You will be notified once verified.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                    html_message=welcome_html,
                )
                
                # Clean up session
                if 'pending_caregiver_id' in request.session:
                    del request.session['pending_caregiver_id']
                
                messages.success(request, 'Registration successful! Your documents will be reviewed by admin.')
                return redirect('accounts:profile', user_id=user.id)
            else:
                # If verification form is invalid, show step 2 again with errors
                return render(request, 'accounts/register_caregiver_step2.html', {
                    'verification_form': verification_form,
                    'step': '2',
                })
    
    # Handle GET request - show the first step of the form
    initial_data = {
        'role': 'caregiver',
        'email': request.GET.get('email', '')
    }
    user_form = CustomUserCreationForm(initial=initial_data)
    
    # Debug: Print form fields to console
    print("Form fields:", user_form.fields.keys())
    print("Email field exists:", 'email' in user_form.fields)
    
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
            form = ProfileForm(request.POST, request.FILES, instance=user)
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
            form = ProfileForm(instance=user)
            verification_form = CaregiverVerificationForm(instance=caregiver_verification)
        verification_status = {
            'reviewed': caregiver_verification.reviewed,
            'approved': caregiver_verification.approved,
            'admin_comment': caregiver_verification.admin_comment,
        }
    else:
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile', user_id=user.id)
            else:
                print(f"Form errors: {form.errors}")
        else:
            form = ProfileForm(instance=user)
    # Safely handle profile picture access
    profile_picture_url = None
    if user.profile_picture:
        try:
            # Just get the name without accessing file
            print(f"Profile picture found: {user.profile_picture.name}")
            # Use build_absolute_uri to construct the URL instead of .url
            from django.urls import reverse
            from django.conf import settings
            from urllib.parse import urljoin
            profile_picture_url = urljoin(settings.MEDIA_URL, user.profile_picture.name)
        except Exception as e:
            print(f"Error accessing profile picture: {str(e)}")
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
    # Find existing connection request from request.user to user (if any)
    existing_request = None
    if request.user.is_authenticated and hasattr(request.user, 'sent_connection_requests') and user.is_caregiver and request.user != user and hasattr(user, 'is_caregiver') and user.is_caregiver():
        try:
            existing_request = request.user.sent_connection_requests.filter(to_user=user).first()
        except Exception as e:
            existing_request = None
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
        'profile_picture_url': profile_picture_url,
        'existing_request': existing_request,
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
def update_profile(request):
    """
    Handle profile updates from the profile page
    """
    if request.method == 'POST':
        user = request.user
        form = ProfileForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Your profile has been updated successfully.')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('accounts:profile', user_id=user.id)
        else:
            # If form is not valid, show the errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('accounts:profile', user_id=user.id)
    
    return redirect('accounts:profile', user_id=request.user.id)

@login_required
def update_contact(request):
    """
    Handle contact information updates from the profile page
    """
    if request.method == 'POST':
        user = request.user
        
        # Update the fields directly from request.POST
        email = request.POST.get('email')
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # Basic validation
        if email:
            user.email = email
        
        # Clean and validate phone number if provided
        if phone:
            # Simple validation - you might want to enhance this
            if not phone.startswith('+') or len(phone) < 10:
                messages.error(request, 'Please enter a valid phone number with country code (e.g., +9779812345678)')
                return redirect('accounts:profile', user_id=user.id)
            user.phone = phone
        else:
            user.phone = ''  # Clear the phone number if empty
            
        # Update address
        user.address = address
        
        try:
            user.save()
            messages.success(request, 'Your contact information has been updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating contact information: {str(e)}')
        
        return redirect('accounts:profile', user_id=user.id)
    
    return redirect('accounts:profile', user_id=request.user.id)

@login_required
def change_password(request):
    """
    Handle password change
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile', user_id=request.user.id)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {
        'form': form,
        'emergency_contacts': request.user.emergency_contacts.all() if request.user.is_authenticated else []
    })

@login_required
def privacy_settings(request):
    """
    Handle privacy settings
    """
    if request.method == 'POST':
        form = PrivacySettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your privacy settings have been updated.')
            return redirect('accounts:privacy_settings')
    else:
        form = PrivacySettingsForm(instance=request.user)
    
    return render(request, 'accounts/privacy_settings.html', {
        'form': form,
        'emergency_contacts': request.user.emergency_contacts.all() if request.user.is_authenticated else []
    })

@login_required
def notification_settings(request):
    """
    Handle notification preferences
    """
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your notification preferences have been updated.')
            return redirect('accounts:notification_settings')
    else:
        form = NotificationSettingsForm(instance=request.user)
    
    return render(request, 'accounts/notification_settings.html', {
        'form': form,
        'emergency_contacts': request.user.emergency_contacts.all() if request.user.is_authenticated else []
    })

@login_required
def connected_accounts(request):
    """
    Handle connected accounts (social auth)
    """
    # This is a placeholder - you'll need to implement social auth separately
    return render(request, 'accounts/connected_accounts.html', {
        'emergency_contacts': request.user.emergency_contacts.all() if request.user.is_authenticated else []
    })

@login_required
def verify_email(request):
    """
    Send verification email to the user
    """
    user = request.user
    if user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('accounts:profile', user_id=user.id)
    
    # Generate verification token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build verification URL
    verification_url = request.build_absolute_uri(
        f'/accounts/profile/verify-email/confirm/{uid}/{token}/'
    )
    
    # Send verification email
    subject = 'Verify your email address'
    message = f'Please click the following link to verify your email:\n\n{verification_url}'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    messages.success(request, 'Verification email sent. Please check your inbox.')
    return redirect('accounts:profile', user_id=user.id)


def verify_email_confirm(request, uidb64, token):
    """
    Verify user's email using the token from the verification email
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        messages.success(request, 'Your email has been verified successfully!')
        # Log the user in if they're not already
        if not request.user.is_authenticated:
            login(request, user)
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
    
    return redirect('accounts:profile', user_id=user.id if user else 0)


@login_required
def setup_2fa(request):
    """
    Set up two-factor authentication for the user
    """
    user = request.user
    
    # Generate a random secret key for the user
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save()
    
    # Create a TOTP object
    totp = pyotp.TOTP(user.totp_secret)
    
    # Generate the provisioning URI for the QR code
    provisioning_uri = totp.provisioning_uri(
        name=f"{user.email}",
        issuer_name="Elder Care"
    )
    
    # Generate QR code
    factory = qrcode.image.svg.SvgImage
    img = qrcode.make(provisioning_uri, image_factory=factory)
    stream = BytesIO()
    img.save(stream)
    qr_code_svg = stream.getvalue().decode()
    
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        if code and totp.verify(code, valid_window=1):
            user.two_factor_enabled = True
            user.save()
            # Generate backup codes
            backup_codes = [pyotp.random_base32()[:8].upper() for _ in range(10)]
            request.session['backup_codes'] = backup_codes
            messages.success(request, 'Two-factor authentication has been enabled successfully!')
            return redirect('accounts:backup_codes')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
    
    return render(request, 'accounts/setup_2fa.html', {
        'qr_code_svg': qr_code_svg,
        'secret_key': user.totp_secret,
    })


@login_required
def disable_2fa(request):
    """
    Disable two-factor authentication for the user
    """
    if request.method == 'POST':
        user = request.user
        user.two_factor_enabled = False
        user.totp_secret = ''
        user.save()
        messages.success(request, 'Two-factor authentication has been disabled.')
        return redirect('accounts:profile', user_id=user.id)
    
    return render(request, 'accounts/disable_2fa.html')


def verify_2fa(request):
    """
    Verify the 2FA code entered by the user
    """
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        user = request.user
        
        if user.totp_secret:
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(code, valid_window=1):
                # Store in session that 2FA is verified
                request.session['2fa_verified'] = True
                return redirect('accounts:profile', user_id=user.id)
        
        messages.error(request, 'Invalid verification code. Please try again.')
    
    return render(request, 'accounts/verify_2fa.html')


@login_required
@require_http_methods(['POST'])
def upload_avatar(request):
    """
    Handle avatar upload/removal via AJAX
    """
    try:
        # Handle avatar removal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                if data.get('remove'):
                    # Remove the avatar
                    if request.user.profile_picture:
                        # Delete the file from storage
                        if os.path.isfile(request.user.profile_picture.path):
                            os.remove(request.user.profile_picture.path)
                        # Clear the profile picture field
                        request.user.profile_picture = None
                        request.user.save()
                        return JsonResponse({'success': True, 'message': 'Profile picture removed successfully'})
                    return JsonResponse({'error': 'No profile picture to remove'}, status=400)
            except json.JSONDecodeError:
                pass
        
        # Handle file upload
        if 'avatar' in request.FILES:
            avatar = request.FILES['avatar']
            
            # Validate file size (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                return JsonResponse({'error': 'File size too large. Max 5MB allowed.'}, status=400)
            
            # Validate file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in valid_extensions:
                return JsonResponse({'error': 'Invalid file type. Only JPG, PNG, and GIF are allowed.'}, status=400)
            
            # Create user directory if it doesn't exist
            user_dir = os.path.join(settings.MEDIA_ROOT, 'avatars', f'user_{request.user.id}')
            os.makedirs(user_dir, exist_ok=True)
            
            # Delete old avatar if exists
            if request.user.profile_picture:
                try:
                    if os.path.isfile(request.user.profile_picture.path):
                        os.remove(request.user.profile_picture.path)
                except Exception as e:
                    print(f"Error removing old avatar: {e}")
            
            # Save new avatar
            filename = f'avatar{ext}'
            file_path = os.path.join('avatars', f'user_{request.user.id}', filename)
            
            # Save the file
            file_name = default_storage.save(file_path, ContentFile(avatar.read()))
            
            # Update user's profile picture
            request.user.profile_picture = file_name
            request.user.save()
            
            return JsonResponse({
                'success': True,
                'url': request.user.profile_picture.url,
                'message': 'Profile picture updated successfully!'
            })
        
        return JsonResponse({'error': 'No file provided'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def backup_codes(request):
    """
    Display and manage backup codes for 2FA
    """
    backup_codes = request.session.pop('backup_codes', None)
    
    if request.method == 'POST' and not backup_codes:
        # Generate new backup codes
        backup_codes = [pyotp.random_base32()[:8].upper() for _ in range(10)]
        request.session['backup_codes'] = backup_codes
    
    return render(request, 'accounts/backup_codes.html', {
        'backup_codes': backup_codes,
    })


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
def send_connection_request(request, caregiver_id):
    """
    Send a connection request to a caregiver
    """
    if not request.user.is_authenticated or not request.user.is_family:
        messages.error(request, 'Only family members can send connection requests.')
        return redirect('home')
    
    caregiver = get_object_or_404(User, id=caregiver_id, role='caregiver')
    
    # Check if a request already exists
    existing_request = ConnectionRequest.objects.filter(
        from_user=request.user,
        to_user=caregiver
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            messages.info(request, 'You have already sent a connection request to this caregiver.')
        elif existing_request.status == 'accepted':
            messages.info(request, 'You are already connected with this caregiver.')
        else:  # rejected
            messages.info(request, 'Your previous connection request was declined.')
        return redirect('profile', user_id=caregiver_id)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        
        # Create the connection request
        connection_request = ConnectionRequest.objects.create(
            from_user=request.user,
            to_user=caregiver,
            message=message,
            status='pending'
        )
        
        # Send notification to the caregiver
        send_notification(
            recipient=caregiver,
            title='New Connection Request',
            message=f"{request.user.get_full_name() or request.user.username} has sent you a connection request.",
            url=f'/accounts/connections/requests/'
        )
        
        messages.success(request, 'Connection request sent successfully!')
        return redirect('profile', user_id=caregiver_id)
    
    return render(request, 'accounts/send_connection_request.html', {
        'caregiver': caregiver
    })

@login_required
def connection_requests(request):
    """
    View for caregivers to see their connection requests
    """
    if not request.user.is_authenticated or not request.user.is_caregiver:
        messages.error(request, 'Only caregivers can view connection requests.')
        return redirect('home')
    
    # Get pending connection requests for the current user
    connection_requests = ConnectionRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    return render(request, 'accounts/connection_requests.html', {
        'connection_requests': connection_requests,
        'active_tab': 'connections'
    })

@login_required
@require_http_methods(['POST'])
def respond_to_connection_request(request, request_id, action):
    """
    Handle accepting or rejecting a connection request
    """
    if action not in ['accept', 'reject']:
        messages.error(request, 'Invalid action.')
        return redirect('connection_requests')
    
    try:
        connection_request = ConnectionRequest.objects.get(
            id=request_id,
            to_user=request.user,
            status='pending'
        )
        
        if action == 'accept':
            connection_request.status = 'accepted'
            connection_request.save()
            
            # Create a connection between users
            request.user.connections.add(connection_request.from_user)
            connection_request.from_user.connections.add(request.user)
            
            messages.success(request, f'You are now connected with {connection_request.from_user.get_full_name() or connection_request.from_user.username}!')
            
            # Send notification to the family member
            send_notification(
                recipient=connection_request.from_user,
                title='Connection Accepted',
                message=f"{request.user.get_full_name() or request.user.username} has accepted your connection request.",
                url=f'/profile/{request.user.id}/'
            )
            
        else:  # reject
            connection_request.status = 'rejected'
            connection_request.save()
            messages.info(request, 'Connection request declined.')
        
        return redirect('connection_requests')
        
    except ConnectionRequest.DoesNotExist:
        messages.error(request, 'Connection request not found or already processed.')
        return redirect('connection_requests')

@login_required
def cancel_account_deletion(request):
    if request.method == 'POST':
        try:
            deletion_request = AccountDeletionRequest.objects.get(user=request.user)
            deletion_request.delete()
            messages.success(request, 'Account deletion request has been cancelled.')
        except AccountDeletionRequest.DoesNotExist:
            messages.info(request, 'No active account deletion request found.')
        return redirect('settings')
    return redirect('landing')

@login_required
@require_http_methods(['POST'])
def ajax_upload_profile_picture(request):
    """
    Handle AJAX request for profile picture upload
    """
    if 'profile_picture' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    try:
        # Get the uploaded file
        uploaded_file = request.FILES['profile_picture']
        
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:  # 5MB
            return JsonResponse(
                {'success': False, 'error': 'File size too large. Maximum size is 5MB.'}, 
                status=400
            )
        
        # Validate file type
        valid_image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if uploaded_file.content_type not in valid_image_types:
            return JsonResponse(
                {'success': False, 'error': 'Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.'}, 
                status=400
            )
        
        # Process the image (resize and convert to webp for better performance)
        try:
            # Open the uploaded image
            img = Image.open(uploaded_file)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize the image to a maximum of 800x800 while maintaining aspect ratio
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save the processed image to a BytesIO buffer
            output = BytesIO()
            img.save(output, format='WEBP', quality=85, optimize=True)
            output.seek(0)
            
            # Create a new InMemoryUploadedFile with the processed image
            file_name = f"profile_{request.user.id}.webp"
            file = InMemoryUploadedFile(
                output,
                'ImageField',
                file_name,
                'image/webp',
                sys.getsizeof(output),
                None
            )
            
            # Get the user instance
            user = request.user
            
            # Delete old profile picture if it exists
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            
            # Save the new profile picture
            user.profile_picture.save(file_name, file, save=True)
            
            # Return success response with the new image URL
            return JsonResponse({
                'success': True,
                'image_url': user.profile_picture.url,
                'message': 'Profile picture updated successfully!'
            })
            
        except Exception as e:
            return JsonResponse(
                {'success': False, 'error': f'Error processing image: {str(e)}'}, 
                status=500
            )
            
    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)}, 
            status=500
        )

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
