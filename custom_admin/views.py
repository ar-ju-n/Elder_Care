from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout, authenticate, get_user_model, login
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db import transaction, connection, OperationalError 
from django.utils import timezone
from django.conf import settings 
from django.db.models import Q
import csv
import os 
from core.models import SystemSetting, AuditLog, NotificationTemplate, ScheduledNotification, BrandingSetting
from core.forms import BrandingSettingForm
# If you need Event, Content, Resident, etc., import them from their correct app (e.g., from events.models import Event)
from accounts.models import CaregiverVerification


User = get_user_model()

def integration_management(request):
    return render(request, 'custom_admin/integration_management.html')

# Helper: Only allow admin users (superusers or staff)
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def integration_list(request):
    if request.method == 'GET':
        integrations = list(Integration.objects.all().values())
        return JsonResponse({'integrations': integrations})

@login_required
@user_passes_test(is_admin)
def integration_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = AdminIntegrationForm(data)
        if form.is_valid():
            integration = form.save()
            return JsonResponse({'success': True, 'integration': integration.id})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@user_passes_test(is_admin)
def integration_edit(request, pk):
    integration = get_object_or_404(Integration, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        form = AdminIntegrationForm(data, instance=integration)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@user_passes_test(is_admin)
def integration_delete(request, pk):
    integration = get_object_or_404(Integration, pk=pk)
    if request.method == 'POST':
        integration.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
@user_passes_test(is_admin)
def integration_connect(request, pk):
    integration = get_object_or_404(Integration, pk=pk)
    # This is a stub for 'connect' logic; implement provider-specific logic here
    if request.method == 'POST':
        integration.status = 'Connected'
        integration.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=405)

# Helper to get the current branding setting
def get_branding_setting():
    return BrandingSetting.objects.first()

from django.core.mail import send_mail

from django.urls import reverse

def notify_user(user, subject, message, url=None, job_id=None, request=None):
    from core.models import Notification
    from django.urls import reverse
    # If job_id is provided, generate the appropriate job detail URL
    if job_id is not None:
        user_role = getattr(user, 'role', None)
        if user_role == 'caregiver' or user_role == 'family':
            url = reverse('jobs:job_detail', args=[job_id])
        else:
            url = reverse('custom_admin:job_detail', args=[job_id])
        # Prepend domain if needed
        if request is not None:
            url = request.build_absolute_uri(url)
        else:
            url = f'http://127.0.0.1:8000{url}'
    elif url and not url.startswith('http'):
        url = f'http://127.0.0.1:8000{url}'
    Notification.objects.create(
        recipient=user,
        subject=subject,
        message=message,
        url=url
    )
    # Send email
    if user.email:
        send_mail(subject, message, 'no-reply@eldercare.com', [user.email])

from django.views.decorators.http import require_POST
from .models import Integration
from .forms import AdminIntegrationForm
import json

# --- Custom Admin Login View ---
from django.shortcuts import render, redirect
from django.contrib import messages

def custom_admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('custom_admin:dashboard')  # Change as needed
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')
    return render(request, 'custom_admin/login.html')

# --- Communication Moderation API ---
from chat.models import ChatMessage
from forum.models import Reply
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def api_moderation_messages(request):
    if request.method == "GET":
        status = request.GET.get('status', 'pending')  # pending, flagged, all
        qs = ChatMessage.objects.all()
        if status == 'pending':
            qs = qs.filter(is_approved=False)
        elif status == 'flagged':
            qs = qs.filter(is_flagged=True)
        messages = list(qs.order_by('-timestamp').values(
            'id', 'sender_id', 'message', 'timestamp', 'is_approved', 'is_flagged', 'moderation_notes'))
        return JsonResponse({'messages': messages})
    else:  # POST: moderate
        data = json.loads(request.body)
        msg_id = data.get('id')
        action = data.get('action')  # approve, reject, flag, delete, note
        notes = data.get('notes', '')
        msg = ChatMessage.objects.filter(id=msg_id).first()
        if not msg:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        if action == 'approve':
            msg.is_approved = True
            msg.is_flagged = False
        elif action == 'reject':
            msg.is_approved = False
            msg.is_flagged = True
        elif action == 'flag':
            msg.is_flagged = True
        elif action == 'delete':
            msg.delete()
            return JsonResponse({'success': True, 'deleted': True})
        if notes:
            msg.moderation_notes = notes
        msg.save()
        return JsonResponse({'success': True})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def api_moderation_replies(request):
    if request.method == "GET":
        status = request.GET.get('status', 'pending')  # pending, flagged, all
        qs = Reply.objects.all()
        if status == 'pending':
            qs = qs.filter(is_approved=False)
        elif status == 'flagged':
            qs = qs.filter(is_flagged=True)
        replies = list(qs.order_by('-created_at').values(
            'id', 'author_id', 'body', 'created_at', 'is_approved', 'is_flagged', 'moderation_notes'))
        return JsonResponse({'replies': replies})
    else:  # POST: moderate
        data = json.loads(request.body)
        reply_id = data.get('id')
        action = data.get('action')  # approve, reject, flag, delete, note
        notes = data.get('notes', '')
        reply = Reply.objects.filter(id=reply_id).first()
        if not reply:
            return JsonResponse({'success': False, 'error': 'Reply not found'}, status=404)
        if action == 'approve':
            reply.is_approved = True
            reply.is_flagged = False
        elif action == 'reject':
            reply.is_approved = False
            reply.is_flagged = True
        elif action == 'flag':
            reply.is_flagged = True
        elif action == 'delete':
            reply.delete()
            return JsonResponse({'success': True, 'deleted': True})
        if notes:
            reply.moderation_notes = notes
        reply.save()
        return JsonResponse({'success': True})

@login_required
@user_passes_test(is_admin)
@require_POST
def download_logs(request):
    # TODO: Implement actual log file streaming
    return JsonResponse({'status': 'success', 'message': 'Logs downloaded (stub).'})

@login_required
@user_passes_test(is_admin)
@require_POST
def clear_cache(request):
    # TODO: Implement cache clearing
    return JsonResponse({'status': 'success', 'message': 'Cache cleared (stub).'})

@login_required
@user_passes_test(is_admin)
@require_POST
def backup_database(request):
    # TODO: Implement DB backup
    return JsonResponse({'status': 'success', 'message': 'Database backup started (stub).'})

@login_required
@user_passes_test(is_admin)
@require_POST
def restore_database(request):
    # TODO: Implement DB restore
    return JsonResponse({'status': 'success', 'message': 'Database restore started (stub).'})

@login_required
@user_passes_test(is_admin)
def resident_management(request):
    from accounts.models import User
    from core.models import AuditLog
    import csv
    from django.http import HttpResponse
    from django.db.models import Q
    # Filters
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    bulk_action = request.POST.get('bulk_action')
    selected_ids = request.POST.getlist('selected')
    export_csv = request.GET.get('export_csv')

    qs = User.objects.filter(role=User.FAMILY)
    if search_query:
        qs = qs.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query) | Q(full_name__icontains=search_query))
    if start_date:
        qs = qs.filter(date_joined__gte=start_date)
    if end_date:
        qs = qs.filter(date_joined__lte=end_date)

    # Bulk actions
    if bulk_action and selected_ids:
        users = User.objects.filter(id__in=selected_ids, role=User.FAMILY)
        if bulk_action == 'activate':
            users.update(is_active=True)
            for u in users:
                AuditLog.objects.create(user=request.user, action='edit', target_type='user', target_id=u.id, target_repr=u.username, details='Bulk activated resident (family) account.')
        elif bulk_action == 'deactivate':
            users.update(is_active=False)
            for u in users:
                AuditLog.objects.create(user=request.user, action='edit', target_type='user', target_id=u.id, target_repr=u.username, details='Bulk deactivated resident (family) account.')
        elif bulk_action == 'delete':
            for u in users:
                AuditLog.objects.create(user=request.user, action='delete', target_type='user', target_id=u.id, target_repr=u.username, details='Bulk deleted resident (family) account.')
            users.delete()
        return redirect(request.path)

    # CSV Export
    if export_csv == '1':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="residents.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Active', 'Date Joined', 'Last Login'])
        for u in qs:
            writer.writerow([
                u.id, u.username, u.email, u.full_name, u.is_active, u.date_joined, u.last_login
            ])
        return response

    # Prepare data for template
    residents = qs.order_by('-date_joined')
    context = {
        'residents': residents,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'custom_admin/resident_management.html', context)

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    # Placeholder for dashboard (analytics, quick links, etc.)
    return render(request, 'custom_admin/dashboard.html')

from accounts.models import User, CaregiverVerification
from .forms import AdminUserEditForm, UserRoleForm
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

@login_required
@user_passes_test(is_admin)
def user_roles_edit(request, user_id):
    """
    View to edit user roles and permissions in the admin panel.
    """
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit user roles.')
        return redirect('custom_admin:user_management')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=user)
        if form.is_valid():
            # Save basic user info
            user = form.save(commit=False)
            
            # Handle groups
            user.groups.clear()
            for group in form.cleaned_data['groups']:
                user.groups.add(group)
            
            # Handle user permissions
            user.user_permissions.clear()
            for permission in form.cleaned_data['user_permissions']:
                user.user_permissions.add(permission)
            
            user.save()
            
            # Log the action
            log_admin_action(
                request.user,
                f'Updated roles and permissions for user {user.get_full_name() or user.email} (ID: {user.id})',
                f'Updated groups: {list(user.groups.values_list("name", flat=True))}\nUpdated permissions: {list(user.user_permissions.values_list("codename", flat=True))}'
            )
            
            messages.success(request, 'User roles and permissions updated successfully.')
            return redirect('custom_admin:user_management')
    else:
        form = UserRoleForm(instance=user)
    
    context = {
        'title': f'Edit Roles & Permissions: {user.get_full_name() or user.email}',
        'form': form,
        'user': user,
    }
    return render(request, 'custom_admin/user_roles_edit.html', context)


def user_management(request):
    from core.models import AuditLog
    users = User.objects.all().order_by('-date_joined')
    edit_user = None
    edit_form = None
    action = request.GET.get('action')
    user_id = request.GET.get('user_id')

    # Handle actions: edit, delete, approve, reset password
    if action and user_id:
        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            messages.error(request, 'User not found.')
            return redirect('custom_admin:user_management')

        if action == 'edit':
            if request.method == 'POST':
                edit_form = AdminUserEditForm(request.POST, instance=target_user)
                if edit_form.is_valid():
                    edit_form.save()
                    AuditLog.objects.create(user=request.user, action='edit', target_type='user', target_id=target_user.id, target_repr=target_user.username, details='User details edited.')
        if 'add_article' in request.POST:
            article_form = AdminArticleForm(request.POST)
            if article_form.is_valid():
                article_form.save()
                messages.success(request, 'Article added successfully.')
                return redirect('custom_admin:content_management')
        elif 'edit_article_id' in request.POST:
            article = get_object_or_404(Article, id=request.POST.get('edit_article_id'))
            article_form = AdminArticleForm(request.POST, instance=article)
            if article_form.is_valid():
                article_form.save()
                messages.success(request, 'Article updated successfully.')
                return redirect('custom_admin:content_management')
            edit_article = article
        elif 'delete_article_id' in request.POST:
            article = get_object_or_404(Article, id=request.POST.get('delete_article_id'))
            article.delete()
            messages.success(request, 'Article deleted.')
            return redirect('custom_admin:content_management')
        elif 'add_link' in request.POST:
            link_form = AdminLinkForm(request.POST)
            if link_form.is_valid():
                link_form.save()
                messages.success(request, 'Link added successfully.')
                return redirect('custom_admin:content_management')
        elif 'edit_link_id' in request.POST:
            link = get_object_or_404(Link, id=request.POST.get('edit_link_id'))
            link_form = AdminLinkForm(request.POST, instance=link)
            if link_form.is_valid():
                link_form.save()
                messages.success(request, 'Link updated successfully.')
                return redirect('custom_admin:content_management')
            edit_link = link
        elif 'delete_link_id' in request.POST:
            link = get_object_or_404(Link, id=request.POST.get('delete_link_id'))
            link.delete()
            messages.success(request, 'Link deleted.')
            return redirect('custom_admin:content_management')
    # If GET with ?edit_article or ?edit_link
    if request.method == 'GET':
        if 'edit_article' in request.GET:
            edit_article = get_object_or_404(Article, id=request.GET.get('edit_article'))
            article_form = AdminArticleForm(instance=edit_article)
        if 'edit_link' in request.GET:
            edit_link = get_object_or_404(Link, id=request.GET.get('edit_link'))
            link_form = AdminLinkForm(instance=edit_link)
    # Annotate users with role and permissions summary
    user_data = []
    for u in users:
        perms = list(u.user_permissions.values_list('codename', flat=True))
        perms_display = ', '.join(perms[:3]) + (f' (+{len(perms)-3} more)' if len(perms) > 3 else '') if perms else 'None'
        user_data.append({
            'obj': u,
            'role': u.get_role_display() if hasattr(u, 'get_role_display') else u.role,
            'permissions': perms_display,
            'permissions_full': perms,
        })
    # Handle user actions
    if action and user_id:
        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            messages.error(request, 'User not found.')
            return redirect('custom_admin:user_management')
        if action == 'edit':
            if request.method == 'POST':
                edit_form = AdminUserEditForm(request.POST, instance=target_user)
                if edit_form.is_valid():
                    edit_form.save()
                    AuditLog.objects.create(user=request.user, action='edit', target_type='user', target_id=target_user.id, target_repr=target_user.username, details='User details edited.')
                    messages.success(request, 'User details updated.')
                    return redirect('custom_admin:user_management')
            edit_user = target_user
            edit_form = AdminUserEditForm(instance=target_user)
        elif action == 'delete':
            log_admin_action(request.user, 'delete user', f'Deleted user: {target_user.username} (ID: {target_user.id})')
            target_user.delete()
            messages.success(request, 'User deleted.')
            return redirect('custom_admin:user_management')
        elif action == 'approve_caregiver':
            if not hasattr(target_user, 'caregiver_verification'):
                messages.error(request, f'User {target_user.username} has no caregiver verification record.')
                return redirect('custom_admin:user_management')
            verification = getattr(target_user, 'caregiver_verification', None)
            if not verification:
                messages.error(request, f'Caregiver verification object missing for user {target_user.username}.')
                return redirect('custom_admin:user_management')
            verification.approved = True
            verification.reviewed = True
            verification.save()
            target_user.is_verified = True
            target_user.verified_at = timezone.now()
            target_user.save()
            log_admin_action(request.user, 'approve caregiver', f'Approved caregiver: {target_user.username} (ID: {target_user.id})')
            messages.success(request, f'Caregiver {target_user.username} approved successfully.')
            return redirect('custom_admin:user_management')
        elif action == 'decline_caregiver':
            if not hasattr(target_user, 'caregiver_verification'):
                messages.error(request, f'User {target_user.username} has no caregiver verification record.')
                return redirect('custom_admin:user_management')
            verification = getattr(target_user, 'caregiver_verification', None)
            if not verification:
                messages.error(request, f'Caregiver verification object missing for user {target_user.username}.')
                return redirect('custom_admin:user_management')
            verification.approved = False
            verification.reviewed = True
            verification.save()
            # Also mark the user as not verified
            target_user.is_verified = False
            target_user.save()
            log_admin_action(request.user, 'decline caregiver', f'Declined caregiver: {target_user.username} (ID: {target_user.id})')
            messages.info(request, f'Caregiver {target_user.username} declined.')
            return redirect('custom_admin:user_management')
        elif action == 'reset_password':
            target_user.set_password('NewTempPass123')
            target_user.save()
            log_admin_action(request.user, 'reset password', f'Reset password for user: {target_user.username} (ID: {target_user.id}) to NewTempPass123')
            messages.success(request, 'Password reset to NewTempPass123.')
            return redirect('custom_admin:user_management')

    context = {
        'users_data': user_data,
        'edit_user': edit_user,
        'edit_form': edit_form,
    }
    return render(request, 'custom_admin/user_management.html', context)


from .forms import AdminEventForm, AdminNotificationForm, AdminLinkForm
from content.models import Article, Video, HomepageSlide, Link
from content.forms import ArticleForm, VideoForm, HomepageSlideForm, GuideForm, FAQForm
from content.models import Guide, FAQ

@login_required
@user_passes_test(is_admin)
def link_list(request):
    links = Link.objects.all().order_by('title')
    return render(request, 'custom_admin/link_list.html', {'links': links})

@login_required
@user_passes_test(is_admin)
def link_add(request):
    if request.method == 'POST':
        form = AdminLinkForm(request.POST)
        if form.is_valid():
            link = form.save()
            messages.success(request, 'Link added successfully.')
            return redirect('custom_admin:link_list')
    else:
        form = AdminLinkForm()
    return render(request, 'custom_admin/link_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def link_edit(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    if request.method == 'POST':
        form = AdminLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, 'Link updated successfully.')
            return redirect('custom_admin:link_list')
    else:
        form = AdminLinkForm(instance=link)
    return render(request, 'custom_admin/link_edit.html', {'form': form, 'link': link})

@login_required
@user_passes_test(is_admin)
def link_delete(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    if request.method == 'POST':
        link.delete()
        messages.success(request, 'Link deleted successfully.')
        return redirect('custom_admin:link_list')
    return render(request, 'custom_admin/confirm_delete.html', {'object': link, 'type': 'Link'})

@login_required
@user_passes_test(is_admin)
def slide_list(request):
    slides = HomepageSlide.objects.all().order_by('ordering')
    return render(request, 'custom_admin/slide_list.html', {'slides': slides})

@login_required
@user_passes_test(is_admin)
def slide_add(request):
    if request.method == 'POST':
        form = HomepageSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save()
            messages.success(request, 'Homepage slide added successfully.')
            return redirect('custom_admin:slide_list')
    else:
        form = HomepageSlideForm()
    return render(request, 'custom_admin/slide_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def slide_edit(request, slide_id):
    slide = get_object_or_404(HomepageSlide, id=slide_id)
    if request.method == 'POST':
        form = HomepageSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Homepage slide updated successfully.')
            return redirect('custom_admin:slide_list')
    else:
        form = HomepageSlideForm(instance=slide)
    return render(request, 'custom_admin/slide_edit.html', {'form': form, 'slide': slide})

@login_required
@user_passes_test(is_admin)
def slide_delete(request, slide_id):
    slide = get_object_or_404(HomepageSlide, id=slide_id)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Homepage slide deleted successfully.')
        return redirect('custom_admin:slide_list')
    return render(request, 'custom_admin/confirm_delete.html', {'object': slide, 'type': 'Homepage Slide'})

@login_required
@user_passes_test(is_admin)
def add_tag(request):
    from content.models import Tag
    from django.http import JsonResponse
    
    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        if tag_name:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            return JsonResponse({
                'success': True,
                'tag': {'id': tag.id, 'name': tag.name},
                'created': created
            })
        return JsonResponse({'success': False, 'error': 'Tag name is required'}, status=400)
    return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def tag_list(request):
    from content.models import Tag
    from django.core.paginator import Paginator
    from django.db.models import Count
    from django.db.models import Q
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all tags with usage count
    tags = Tag.objects.annotate(usage_count=Count('articles')).order_by('name')
    
    # Filter by search query if provided
    if search_query:
        tags = tags.filter(name__icontains=search_query)
    
    # Paginate results
    paginator = Paginator(tags, 15)  # Show 15 tags per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'custom_admin/tag_list.html', {
        'tags': page_obj,
        'search_query': search_query
    })

@login_required
@user_passes_test(is_admin)
def tag_add(request):
    from content.models import Tag
    
    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        if tag_name:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                messages.success(request, f'Tag "{tag_name}" created successfully.')
            else:
                messages.info(request, f'Tag "{tag_name}" already exists.')
            return redirect('custom_admin:tag_list')
        else:
            messages.error(request, 'Tag name is required.')
    
    return redirect('custom_admin:tag_list')

@login_required
@user_passes_test(is_admin)
def tag_edit(request, tag_id):
    from content.models import Tag
    from django.shortcuts import get_object_or_404
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        if not tag_name:
            messages.error(request, 'Tag name is required.')
            return redirect('custom_admin:tag_edit', tag_id=tag_id)
        tag.name = tag_name
        tag.save()
        messages.success(request, f'Tag updated successfully to "{tag_name}".')
        return redirect('custom_admin:tag_list')
    else:
        # Render edit page with tag object
        return render(request, 'custom_admin/tag_edit.html', {'tag': tag})

@login_required
@user_passes_test(is_admin)
def tag_delete(request, tag_id):
    from content.models import Tag
    from django.shortcuts import get_object_or_404
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag_name = tag.name
        tag.delete()
        messages.success(request, f'Tag "{tag_name}" deleted successfully.')
        return redirect('custom_admin:tag_list')
    else:
        # Render confirmation page
        return render(request, 'custom_admin/confirm_delete_tag.html', {'object': tag})

@login_required
@user_passes_test(is_admin)
def article_list(request):
    articles = Article.objects.all().order_by('-published_at')
    return render(request, 'custom_admin/article_list.html', {'articles': articles})

@login_required
@user_passes_test(is_admin)
def article_add(request):
    from content.models import Tag
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            messages.success(request, 'Article added successfully.')
            return redirect('custom_admin:article_list')
    else:
        form = ArticleForm()
    tags = Tag.objects.all().order_by('name')
    return render(request, 'custom_admin/article_add.html', {'form': form, 'tags': tags})

@login_required
@user_passes_test(is_admin)
def article_edit(request, article_id):
    from content.models import Tag
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('custom_admin:article_list')
    else:
        form = ArticleForm(instance=article)
    tags = Tag.objects.all().order_by('name')
    return render(request, 'custom_admin/article_edit.html', {'form': form, 'tags': tags, 'article': article})

@login_required
@user_passes_test(is_admin)
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
        return redirect('custom_admin:article_list')
    return render(request, 'custom_admin/confirm_delete_article.html', {'object': article, 'type': 'Article'})

@login_required
@user_passes_test(is_admin)
def video_list(request):
    from django.core.paginator import Paginator
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Filter videos based on search query
    videos = Video.objects.all().order_by('-published_at')
    if search_query:
        videos = videos.filter(Q(title__icontains=search_query) | Q(tags__name__icontains=search_query)).distinct()
    
    # Paginate results
    paginator = Paginator(videos, 10)  # Show 10 videos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'custom_admin/video_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_videos': videos.count()
    })

@login_required
@user_passes_test(is_admin)
def video_add(request):
    from content.models import Tag
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()
            messages.success(request, 'Video added successfully.')
            return redirect('custom_admin:video_list')
    else:
        form = VideoForm()
    tags = Tag.objects.all().order_by('name')
    return render(request, 'custom_admin/video_add.html', {'form': form, 'tags': tags})

@login_required
@user_passes_test(is_admin)
def video_edit(request, video_id):
    from content.models import Tag
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            form.save()
            messages.success(request, 'Video updated successfully.')
            return redirect('custom_admin:video_list')
    else:
        form = VideoForm(instance=video)
    tags = Tag.objects.all().order_by('name')
    return render(request, 'custom_admin/video_edit.html', {'form': form, 'tags': tags, 'video': video})

@login_required
@user_passes_test(is_admin)
def video_delete(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Video deleted successfully.')
        return redirect('custom_admin:video_list')
    return render(request, 'custom_admin/confirm_delete.html', {'object': video, 'type': 'Video'})

from events.models import Event
from accounts.models import Notification

@user_passes_test(is_admin)
def content_management(request):
    # Redirect to the new dedicated content management pages
    messages.info(request, 'Please use the new dedicated content management pages for Videos, Articles, Links, and Homepage Slides.')
    return redirect('custom_admin:video_list')

    # Handle tag creation
    if request.method == 'POST' and 'tag_name' in request.POST:
        tag_name = request.POST.get('tag_name', '').strip()
        if tag_name:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                log_admin_action(request.user, 'add tag', f'Added tag: {tag.name} (ID: {tag.id})')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                tags = list(Tag.objects.all().order_by('name').values('id', 'name'))
                return JsonResponse({'success': True, 'tags': tags, 'created': created})
            if created:
                messages.success(request, f'Tag "{tag_name}" created successfully.')
            else:
                messages.info(request, f'Tag "{tag_name}" already exists.')
            return redirect('custom_admin:content_management')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Tag name cannot be empty.'})
            tag_form_errors = 'Tag name cannot be empty.'

    # Handle tag edit
    if request.method == 'POST' and 'edit_tag_id' in request.POST:
        tag_id = request.POST.get('edit_tag_id')
        tag_name = request.POST.get('edit_tag_name', '').strip()
        try:
            tag = Tag.objects.get(id=tag_id)
            if tag_name:
                old_name = tag.name
                tag.name = tag_name
                tag.save()
                log_admin_action(request.user, 'edit tag', f'Edited tag: {old_name} (ID: {tag.id}) → {tag.name}')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    tags = list(Tag.objects.all().order_by('name').values('id', 'name'))
                    return JsonResponse({'success': True, 'tags': tags})
                messages.success(request, f'Tag updated to "{tag_name}".')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Tag name cannot be empty.'})
                tag_form_errors = 'Tag name cannot be empty.'
        except Tag.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Tag not found.'})
            messages.error(request, 'Tag not found.')
        return redirect('custom_admin:content_management')

    # Handle tag delete
    if request.method == 'POST' and 'delete_tag_id' in request.POST:
        tag_id = request.POST.get('delete_tag_id')
        try:
            tag = Tag.objects.get(id=tag_id)
            log_admin_action(request.user, 'delete tag', f'Deleted tag: {tag.name} (ID: {tag.id})')
            tag.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                tags = list(Tag.objects.all().order_by('name').values('id', 'name'))
                return JsonResponse({'success': True, 'tags': tags})
            messages.success(request, 'Tag deleted.')
        except Tag.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Tag not found.'})
            messages.error(request, 'Tag not found.')
        return redirect('custom_admin:content_management')

    # Handle article creation
    if request.method == 'POST' and 'add_article' in request.POST:
        article_form = ArticleForm(request.POST)
        if article_form.is_valid():
            article = article_form.save()
            log_admin_action(request.user, 'add article', f'Added article: {article.title} (ID: {article.id})')
            messages.success(request, 'Article added successfully.')
            return redirect('custom_admin:content_management')

    # Handle article edit
    if request.method == 'POST' and 'edit_article_id' in request.POST:
        article = Article.objects.get(id=request.POST.get('edit_article_id'))
        article_form = ArticleForm(request.POST, instance=article)
        if article_form.is_valid():
            article = article_form.save()
            log_admin_action(request.user, 'edit article', f'Edited article: {article.title} (ID: {article.id})')
            messages.success(request, 'Article updated successfully.')
            return redirect('custom_admin:content_management')

    # Handle article delete
    if request.method == 'POST' and 'delete_article_id' in request.POST:
        article = Article.objects.get(id=request.POST.get('delete_article_id'))
        log_admin_action(request.user, 'delete article', f'Deleted article: {article.title} (ID: {article.id})')
        article.delete()
        messages.success(request, 'Article deleted.')
        return redirect('custom_admin:content_management')

    # Handle link creation
    if request.method == 'POST' and 'add_link' in request.POST:
        link_form = AdminLinkForm(request.POST)
        if link_form.is_valid():
            link = link_form.save()
            log_admin_action(request.user, 'add link', f'Added link: {link.title} (ID: {link.id})')
            messages.success(request, 'Link added successfully.')
            return redirect('custom_admin:content_management')

    # Handle link edit
    if request.method == 'POST' and 'edit_link_id' in request.POST:
        link = Link.objects.get(id=request.POST.get('edit_link_id'))
        link_form = AdminLinkForm(request.POST, instance=link)
        if link_form.is_valid():
            link = link_form.save()
            log_admin_action(request.user, 'edit link', f'Edited link: {link.title} (ID: {link.id})')
            messages.success(request, 'Link updated successfully.')
            return redirect('custom_admin:content_management')

    # Handle link delete
    if request.method == 'POST' and 'delete_link_id' in request.POST:
        link = Link.objects.get(id=request.POST.get('delete_link_id'))
        log_admin_action(request.user, 'delete link', f'Deleted link: {link.title} (ID: {link.id})')
        link.delete()
        messages.success(request, 'Link deleted.')
        return redirect('custom_admin:content_management')

    # Handle video creation
    if request.method == 'POST' and 'add_video' in request.POST:
        video_form = VideoForm(request.POST, request.FILES)
        if video_form.is_valid():
            video = video_form.save()
            log_admin_action(request.user, 'add video', f'Added video: {video.title} (ID: {video.id})')
            messages.success(request, 'Video added successfully.')
            return redirect('custom_admin:content_management')

    # Handle video edit
    if request.method == 'POST' and 'edit_video_id' in request.POST:
        video = Video.objects.get(id=request.POST.get('edit_video_id'))
        video_form = VideoForm(request.POST, request.FILES, instance=video)
        if video_form.is_valid():
            video = video_form.save()
            log_admin_action(request.user, 'edit video', f'Edited video: {video.title} (ID: {video.id})')
            messages.success(request, 'Video updated successfully.')
            return redirect('custom_admin:content_management')

    # Handle video delete
    if request.method == 'POST' and 'delete_video_id' in request.POST:
        video = Video.objects.get(id=request.POST.get('delete_video_id'))
        log_admin_action(request.user, 'delete video', f'Deleted video: {video.title} (ID: {video.id})')
        video.delete()
        messages.success(request, 'Video deleted.')
        return redirect('custom_admin:content_management')

    # Handle slide creation
    if request.method == 'POST' and 'add_slide' in request.POST:
        homepage_slide_form = HomepageSlideForm(request.POST, request.FILES)
        if homepage_slide_form.is_valid():
            slide = homepage_slide_form.save()
            log_admin_action(request.user, 'add slide', f'Added slide: {slide.title} (ID: {slide.id})')
            messages.success(request, 'Slide added successfully.')
            return redirect('custom_admin:content_management')


    # Handle slide edit
    if request.method == 'POST' and 'edit_slide_id' in request.POST:
        slide = HomepageSlide.objects.get(id=request.POST.get('edit_slide_id'))
        homepage_slide_form = HomepageSlideForm(request.POST, instance=slide)
        if homepage_slide_form.is_valid():
            slide = homepage_slide_form.save()
            log_admin_action(request.user, 'edit slide', f'Edited slide: {slide.title} (ID: {slide.id})')
            messages.success(request, 'Slide updated successfully.')
            return redirect('custom_admin:content_management')

    # Handle slide delete
    if request.method == 'POST' and 'delete_slide_id' in request.POST:
        slide_id = request.POST.get('delete_slide_id')
        try:
            slide = HomepageSlide.objects.get(id=slide_id)
            log_admin_action(request.user, 'delete slide', f'Deleted slide: {slide.title} (ID: {slide.id})')
            slide.delete()
            messages.success(request, f'Slide "{slide.title}" deleted successfully.')
        except HomepageSlide.DoesNotExist:
            messages.error(request, 'Slide not found.')
        return redirect('custom_admin:content_management')

    article_form = ArticleForm()
    articles = Article.objects.all().order_by('-published_at')
    link_form = AdminLinkForm()
    video_form = VideoForm()
    videos = Video.objects.all().order_by('-published_at')
    homepage_slide_form = HomepageSlideForm()
    homepage_slides = HomepageSlide.objects.all().order_by('ordering', 'id')
    tags = Tag.objects.all().order_by('name')
    links = Link.objects.all().order_by('-updated_at')
    context = {
        'article_form': article_form,
        'articles': articles,
        'link_form': link_form,
        'links': links,
        'video_form': video_form,
        'videos': videos,
        'homepage_slide_form': homepage_slide_form,
        'homepage_slides': homepage_slides,
        'tags': tags,
        'tag_form_errors': tag_form_errors,
    }
    return render(request, 'custom_admin/content_management.html', context)




@login_required
@user_passes_test(is_admin)
def event_management(request):
    from core.models import AuditLog
    events = Event.objects.all().order_by('-start_time')
    form = AdminEventForm()
    edit_event = None
    if request.method == 'POST':
        if 'add_event' in request.POST:
            form = AdminEventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.created_by = request.user
                event.save()
                AuditLog.objects.create(
                    user=request.user, action='create', target_type='event', target_id=event.id,
                    target_repr=event.title, details='Event created via admin panel.'
                )
                messages.success(request, 'Event added successfully.')
                return redirect('custom_admin:event_management')
        elif 'edit_event_id' in request.POST:
            event = Event.objects.get(id=request.POST.get('edit_event_id'))
            form = AdminEventForm(request.POST, instance=event)
            if form.is_valid():
                form.save()
                AuditLog.objects.create(
                    user=request.user, action='edit', target_type='event', target_id=event.id,
                    target_repr=event.title, details='Event edited via admin panel.'
                )
                messages.success(request, 'Event updated successfully.')
                return redirect('custom_admin:event_management')
    elif request.GET.get('action') == 'edit' and request.GET.get('event_id'):
        edit_event = Event.objects.get(id=request.GET['event_id'])
        form = AdminEventForm(instance=edit_event)
    elif request.GET.get('action') == 'delete' and request.GET.get('event_id'):
        event_id = request.GET['event_id']
        event = Event.objects.filter(id=event_id).first()
        if event:
            AuditLog.objects.create(
                user=request.user, action='delete', target_type='event', target_id=event.id,
                target_repr=event.title, details='Event deleted via admin panel.'
            )
            event.delete()
        messages.success(request, 'Event deleted.')
        return redirect('custom_admin:event_management')

    context = {
        'events': events,
        'form': form,
        'edit_event': edit_event,
    }
    return render(request, 'custom_admin/event_management.html', context)

@login_required
@user_passes_test(is_admin)
def event_view(request, event_id):
    from events.models import Event
    from django.shortcuts import get_object_or_404
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'custom_admin/event_view.html', {'event': event})


@login_required
@user_passes_test(is_admin)
def notification_management(request):
    from django.db.models import Q
    from accounts.models import User
    from core.forms import AdminNotificationForm, NotificationTemplateForm
    from core.models import NotificationTemplate, ScheduledNotification
    notifications = Notification.objects.all().order_by('-created_at')
    notif_form = AdminNotificationForm()
    template_form = NotificationTemplateForm()
    templates = NotificationTemplate.objects.all()

    # Filtering
    recipient_id = request.GET.get('recipient')
    is_read = request.GET.get('is_read')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if recipient_id:
        notifications = notifications.filter(recipient_id=recipient_id)
    if is_read == 'read':
        notifications = notifications.filter(is_read=True)
    elif is_read == 'unread':
        notifications = notifications.filter(is_read=False)
    if date_from:
        notifications = notifications.filter(created_at__gte=date_from)
    if date_to:
        notifications = notifications.filter(created_at__lte=date_to)

    # Handle POST actions: send, schedule, save template
    if request.method == 'POST':
        if 'save_template' in request.POST:
            template_form = NotificationTemplateForm(request.POST)
            if template_form.is_valid():
                template = template_form.save(commit=False)
                template.created_by = request.user
                template.save()
                messages.success(request, 'Template saved.')
                return redirect('custom_admin:notification_management')
        else:
            notif_form = AdminNotificationForm(request.POST)
            if notif_form.is_valid():
                recipients = notif_form.cleaned_data['recipients']
                subject = notif_form.cleaned_data['subject']
                body = notif_form.cleaned_data['body']
                scheduled_for = notif_form.cleaned_data['scheduled_for']
                template = notif_form.cleaned_data['template']
                if scheduled_for:
                    # Schedule notification
                    scheduled = Schedulednotify_user(
                        subject=subject, body=body, scheduled_for=scheduled_for, created_by=request.user, template=template
                    )
                    scheduled.recipients.set(recipients)
                    messages.success(request, f'Notification scheduled for {scheduled_for}.')
                else:
                    # Send immediately
                    for user in recipients:
                        notify_user(
                            recipient=user,
                            message=f"{subject}\n\n{body}",
                            url=""
                        )
                    messages.success(request, f'Notification sent to {recipients.count()} users.')
                return redirect('custom_admin:notification_management')
    elif request.GET.get('action') == 'delete' and request.GET.get('notif_id'):
        Notification.objects.filter(id=request.GET['notif_id']).delete()
        messages.success(request, 'Notification deleted.')
        return redirect('custom_admin:notification_management')

    recipients = User.objects.all()
    from core.models import ScheduledNotification
    scheduled_notifications = ScheduledNotification.objects.order_by('-scheduled_for')[:20]
    context = {
        'notifications': notifications,
        'notif_form': notif_form,
        'template_form': template_form,
        'templates': templates,
        'recipients': recipients,
        'scheduled_notifications': scheduled_notifications,
        'selected_recipient': recipient_id,
        'selected_is_read': is_read,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
    }
    return render(request, 'custom_admin/notification_management.html', context)

import csv
from django.http import HttpResponse, StreamingHttpResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

@login_required
@user_passes_test(is_admin)
def reporting(request):
    from accounts.models import User
    from events.models import Event
    from django.utils import timezone
    from datetime import timedelta
    from core.models import AuditLog
    # Stats
    total_users = User.objects.count()
    caregivers = User.objects.filter(role=User.CAREGIVER).count()
    families = User.objects.filter(role=User.FAMILY).count()
    admins = User.objects.filter(role=User.ADMIN).count()
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_time__gte=timezone.now()).count()
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_events = Event.objects.order_by('-created_at')[:10]
    # Analytics: user registrations and event creations in last 30 days
    today = timezone.now().date()
    last_30 = today - timedelta(days=29)
    user_trends = (
        User.objects.filter(date_joined__date__gte=last_30)
        .annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    event_trends = (
        Event.objects.filter(created_at__date__gte=last_30)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    # Activity log: show recent user logins (if available), event creations
    user_activity = User.objects.order_by('-last_login')[:10]
    event_activity = Event.objects.order_by('-created_at')[:10]
    audit_logs = AuditLog.objects.select_related('user').all()[:20]
    context = {
        'total_users': total_users,
        'caregivers': caregivers,
        'families': families,
        'admins': admins,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'recent_users': recent_users,
        'recent_events': recent_events,
        'user_trends': list(user_trends),
        'event_trends': list(event_trends),
        'user_activity': user_activity,
        'event_activity': event_activity,
        'audit_logs': audit_logs,
    }
    return render(request, 'custom_admin/reporting.html', context)

@login_required
@user_passes_test(is_admin)
def export_users_csv(request):
    from accounts.models import User
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Role', 'Is Active', 'Is Staff', 'Is Superuser', 'Date Joined', 'Last Login'])
    for u in User.objects.all():
        writer.writerow([
            u.id, u.username, u.email, getattr(u, 'full_name', ''), u.role, u.is_active, u.is_staff, u.is_superuser, u.date_joined, u.last_login
        ])
    return response

@login_required
@user_passes_test(is_admin)
def export_events_csv(request):
    from events.models import Event
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Description', 'Start Time', 'End Time', 'Location', 'Created By', 'Created At'])
    for e in Event.objects.all():
        writer.writerow([
            e.id, e.title, e.description, e.start_time, e.end_time, e.location, getattr(e, 'created_by', ''), e.created_at
        ])
    return response

@login_required
@user_passes_test(is_admin)
def communication_oversight(request):
    # Moderate messages, send notifications
    return render(request, 'custom_admin/communication_oversight.html')

@login_required
@user_passes_test(is_admin)
def billing_controls(request):
    # Financial/billing controls (if applicable)
    return render(request, 'custom_admin/billing_controls.html')

@login_required
@user_passes_test(is_admin)
def notification_template_api(request, id):
    # Ensure only core.models.Notification is used
    Template
    try:
        template = NotificationTemplate.objects.get(id=id)
        return JsonResponse({'subject': template.subject, 'body': template.body})
    except NotificationTemplate.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

import csv
from accounts.models import User
from events.models import Event
from core.forms import UserCSVImportForm, EventCSVImportForm
import csv
from django.http import HttpResponse
from django.utils import timezone

@login_required
@user_passes_test(is_admin)
def export_users(request):
    """
    Export users to a CSV file with basic user information.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Get all users
    users = User.objects.all().order_by('date_joined')
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Role', 'Is Active', 'Date Joined'])
    
    # Write user data
    for user in users:
        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.role,
            'Yes' if user.is_active else 'No',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else ''
        ])
    
    return response


def user_import(request):
    result = None
    errors = []
    if request.method == 'POST':
        form = UserCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            decoded = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
            created, failed = 0, 0
            for row in reader:
                try:
                    user, created_flag = User.objects.get_or_create(
                        username=row.get('username'),
                        defaults={
                            'email': row.get('email'),
                            'role': row.get('role', User.FAMILY),
                            'is_active': row.get('is_active', '1') in ['1', 'True', 'true'],
                        },
                    )
                    if created_flag:
                        created += 1
                    else:
                        failed += 1
                        errors.append(f"Duplicate username: {row.get('username')}")
                except Exception as e:
                    failed += 1
                    errors.append(str(e))
            result = {'created': created, 'failed': failed}
    else:
        form = UserCSVImportForm()
    return render(request, 'custom_admin/user_import.html', {'form': form, 'result': result, 'errors': errors})

@login_required
@user_passes_test(is_admin)
def event_import(request):
    result = None
    errors = []
    if request.method == 'POST':
        form = EventCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            decoded = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
            created, failed = 0, 0
            for row in reader:
                try:
                    event = Event.objects.create(
                        title=row.get('title'),
                        description=row.get('description', ''),
                        start_time=row.get('start_time'),
                        end_time=row.get('end_time'),
                        location=row.get('location', ''),
                    )
                    created += 1
                except Exception as e:
                    failed += 1
                    errors.append(str(e))
            result = {'created': created, 'failed': failed}
    else:
        form = EventCSVImportForm()
    return render(request, 'custom_admin/event_import.html', {'form': form, 'result': result, 'errors': errors})

@login_required
@user_passes_test(is_admin)
def security_compliance(request):
    query = request.GET.get('q', '')
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    if query:
        logs = logs.filter(action__icontains=query)
    audit_logs = logs[:200]
    return render(request, 'custom_admin/security_compliance.html', {'audit_logs': audit_logs, 'query': query})

@login_required
@user_passes_test(is_admin)
def export_audit_logs_csv(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Action', 'Timestamp', 'Details'])
    for log in logs:
        writer.writerow([
            log.id,
            str(log.user) if log.user else '',
            log.action,
            log.timestamp,
            log.details,
        ])
    return response

# Helper: Log an admin action
def log_admin_action(user, action, details=None):
    AuditLog.objects.create(user=user, action=action, details=details or '')

from core.models import SystemSetting
from core.forms import SystemSettingForm

@login_required
@user_passes_test(is_admin)
def customization_settings(request):
    settings = SystemSetting.objects.all().order_by('key')
    form = SystemSettingForm()
    edit_setting = None

    if request.method == 'POST':
        if 'edit_setting_id' in request.POST:
            setting = SystemSetting.objects.get(id=request.POST['edit_setting_id'])
            form = SystemSettingForm(request.POST, instance=setting)
            if form.is_valid():
                form.save()
                messages.success(request, f"Setting '{setting.key}' updated.")
                return redirect('custom_admin:customization_settings')
        else:
            form = SystemSettingForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Setting added.')
                return redirect('custom_admin:customization_settings')
    else:
        form = SystemSettingForm()
        branding_setting = get_branding_setting()
        branding_form = BrandingSettingForm(instance=branding_setting)
    context = {
        'settings': settings,
        'form': form,
        'branding_form': branding_form,
        'branding_setting': branding_setting,
    }
    return render(request, 'custom_admin/customization_settings.html', context)
@login_required
@user_passes_test(is_admin)
def impersonate_user(request, user_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to impersonate users.")
        return redirect('custom_admin:user_management')
    try:
        target_user = User.objects.get(id=user_id)
        # Store the original admin's ID and set impersonation flag
        request.session['impersonate_original_id'] = request.user.id
        request.session['is_impersonating'] = True
        orig_admin = request.user
        login(request, target_user)
        messages.info(request, f"You are now impersonating {target_user.get_full_name() or target_user.username}.")
        # Log the impersonation with the original admin as the actor
        AuditLog.objects.create(
            user=orig_admin,
            action='edit',
            target_type='user',
            target_id=target_user.id,
            target_repr=target_user.username,
            details=f"Admin {orig_admin.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('landing')

@login_required
def stop_impersonation(request):
    orig_id = request.session.pop('impersonate_original_id', None)
    User = get_user_model()
    if orig_id:
        try:
            orig_user = User.objects.get(id=orig_id)
            login(request, orig_user)
            messages.info(request, "You have stopped impersonating and are now yourself again.")
            AuditLog.objects.create(
                user=orig_user,
                action='edit',
                target_type='user',
                target_id=request.user.id,
                target_repr=request.user.username,
                details=f"Admin {orig_user.username} stopped impersonating user {request.user.username} (ID {request.user.id})"
            )
        except User.DoesNotExist:
            logout(request)
            messages.warning(request, "Original admin user not found. Please log in again.")
    else:
        logout(request)
        messages.warning(request, "Impersonation session not found. Please log in again.")
    return redirect('custom_admin:user_management')

@login_required
@user_passes_test(is_admin)
def caregiver_verification_list(request):
    from accounts.models import CaregiverVerification
    import csv
    from django.http import HttpResponse
    filter_status = request.GET.get('status', 'pending')
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    qs = CaregiverVerification.objects.all().select_related('user')
    if filter_status == 'pending':
        qs = qs.filter(reviewed=False)
    elif filter_status == 'approved':
        qs = qs.filter(reviewed=True, approved=True)
    elif filter_status == 'rejected':
        qs = qs.filter(reviewed=True, approved=False)
    if search_query:
        qs = qs.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    if start_date:
        qs = qs.filter(submitted_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(submitted_at__date__lte=end_date)
    # Export to CSV
    if request.GET.get('export') == '1':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="caregiver_verifications.csv"'
        writer = csv.writer(response)
        writer.writerow(['Caregiver', 'Email', 'Govt. ID', 'Certification', 'Document URL', 'Submitted', 'Status', 'Admin Comment'])
        for v in qs.order_by('-submitted_at'):
            status = 'Pending' if not v.reviewed else ('Approved' if v.approved else 'Rejected')
            writer.writerow([
                v.user.get_full_name() or v.user.username,
                v.user.email,
                v.government_id_number,
                v.get_certification_type_display(),
                v.document.url if v.document else '',
                v.submitted_at.strftime('%Y-%m-%d %H:%M'),
                status,
                v.admin_comment or '',
            ])
        return response

    # Handle POST actions (approve/reject, bulk)
    if request.method == 'POST':
        action = request.POST.get('action')
        ids = request.POST.getlist('selected')
        comment = request.POST.get('admin_comment', '').strip()
        verifications = CaregiverVerification.objects.filter(id__in=ids)
        from django.core.mail import send_mail
        from django.conf import settings
        from accounts.models import Notification
        for v in verifications:
            if not v.reviewed:
                v.reviewed = True
                v.reviewed_at = timezone.now()
                if action == 'approve':
                    v.approved = True
                    v.admin_comment = comment or 'Approved by admin.'
                    status_str = 'approved'
                elif action == 'reject':
                    v.approved = False
                    v.admin_comment = comment or 'Rejected by admin.'
                    status_str = 'rejected'
                v.save()
                AuditLog.objects.create(
                    user=request.user,
                    action='edit',
                    target_type='caregiver_verification',
                    target_id=v.id,
                    target_repr=str(v),
                    details=f"{action.title()}d by admin via bulk action. Comment: {v.admin_comment}"
                )
                # In-app notification
                notif_msg = f"Your caregiver verification has been {status_str}."
                if v.admin_comment:
                    notif_msg += f"\nAdmin comment: {v.admin_comment}"
                notify_user(
                    recipient=v.user,
                    message=notif_msg,
                    url="/accounts/profile/"
                )
                # Email notification
                if v.user.email:
                    subject = f"Your caregiver verification has been {status_str.capitalize()}"
                    email_msg = f"Dear {v.user.get_full_name() or v.user.username},\n\n"
                    email_msg += f"Your caregiver verification request has been {status_str}.\n"
                    if v.admin_comment:
                        email_msg += f"\nAdmin comment: {v.admin_comment}\n"
                    email_msg += "\nYou can view your profile for more details.\n\nBest regards,\nElder Care Admin Team"
                    send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL, [v.user.email], fail_silently=True)
        return redirect(request.path + f'?status={filter_status}')
    context = {
        'verifications': qs.order_by('-submitted_at'),
        'filter': filter_status,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'custom_admin/caregiver_verification_list.html', context)

@login_required
@user_passes_test(is_admin)
def user_role_permission_edit(request, user_id):
    from core.forms import UserRolePermissionForm
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "You do not have permission to edit roles/permissions.")
        return redirect('custom_admin:user_management')
    if request.method == 'POST':
        form = UserRolePermissionForm(request.POST, instance=User.objects.get(id=user_id))
        if form.is_valid():
            before = f"role={User.objects.get(id=user_id).role}, perms={[p.codename for p in User.objects.get(id=user_id).user_permissions.all()]}"
            form.save()
            after = f"role={User.objects.get(id=user_id).role}, perms={[p.codename for p in User.objects.get(id=user_id).user_permissions.all()]}"
            AuditLog.objects.create(
                user=request.user,
                action='edit',
                target_type='user',
                target_id=user_id,
                target_repr=User.objects.get(id=user_id).username,
                details=f"Changed role/permissions: {before} -> {after}"
            )
            messages.success(request, 'Role and permissions updated.')
            return redirect('custom_admin:user_management')
    else:
        form = UserRolePermissionForm(instance=User.objects.get(id=user_id))
    return render(request, 'custom_admin/user_role_permission_edit.html', {'form': form, 'target_user': User.objects.get(id=user_id)})

from jobs.models import Job

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from jobs.models import Job
from django.contrib import messages

def is_custom_admin_or_family(user):
    return user.is_authenticated and (user.role == 'custom_admin' or user.role == 'family')

@login_required
def job_list(request):
    if hasattr(request.user, 'role') and request.user.role == 'caregiver':
        jobs = Job.objects.all()
        user_role = 'caregiver'
    elif hasattr(request.user, 'role') and request.user.role in ['admin', 'staff']:
        jobs = Job.objects.all()
        user_role = request.user.role
    else:
        jobs = Job.objects.filter(posted_by=request.user)
        user_role = getattr(request.user, 'role', 'family')
    unread_notifications = request.user.core_notifications.filter(is_read=False).count()
    return render(request, 'custom_admin/job_list.html', {
        'jobs': jobs,
        'unread_notifications': unread_notifications,
        'user_role': user_role
    })

@login_required
def notification_list(request):
    from core.models import Notification
    from jobs.models import Job
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    # Only show notifications for jobs that still exist or notifications not related to jobs
    filtered_notifications = []
    for n in notifications:
        # If notification has a job link, check if job exists
        if n.url and '/jobs/' in n.url:
            try:
                # Extract job_id from URL (pattern: /jobs/<job_id>/detail/)
                import re
                match = re.search(r'/jobs/(\d+)/detail/', n.url)
                if match:
                    job_id = int(match.group(1))
                    if Job.objects.filter(id=job_id).exists():
                        filtered_notifications.append(n)
                    # else: skip notification
                else:
                    filtered_notifications.append(n)
            except Exception:
                filtered_notifications.append(n)
        else:
            filtered_notifications.append(n)
    unread_notifications = request.user.core_notifications.filter(is_read=False).count()
    return render(request, 'custom_admin/notification_list.html', {'notifications': filtered_notifications, 'unread_notifications': unread_notifications})

@login_required
def job_create(request):
    if not is_custom_admin_or_family(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('custom_admin:job_list')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        schedule = request.POST.get('schedule')
        location = request.POST.get('location')
        pay = request.POST.get('pay')
        if not title:
            messages.error(request, 'Title is required.')
        else:
            job = Job.objects.create(
                title=title,
                description=description,
                schedule=schedule,
                location=location,
                pay=pay,
                posted_by=request.user,
                approved=True  # Make job visible to caregivers immediately
            )
            # Notify all caregivers
            from accounts.models import User
            # Ensure only core.models.Notification is used

            caregivers = User.objects.filter(role='caregiver')
            for caregiver in caregivers:
                notify_user(
                    caregiver,
                    'New Job Posted',
                    f'A new job "{job.title}" has been posted.',
                    job_id=job.id,
                    request=request
                )
            messages.success(request, 'Job created and caregivers notified.')
            return redirect('custom_admin:job_list')
    return render(request, 'custom_admin/job_form.html', {'action': 'add'})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    can_apply = False
    already_applied = False
    if request.user.role == 'caregiver':
        from jobs.models import Application
        already_applied = Application.objects.filter(job=job, caregiver=request.user).exists()
        can_apply = not already_applied
    return render(request, 'custom_admin/job_detail.html', {'job': job, 'can_apply': can_apply, 'already_applied': already_applied})

@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    from jobs.models import Application
    from django.urls import reverse
    # Ensure only core.models.Notification is used

    if request.user.role != 'caregiver':
        messages.error(request, 'Only caregivers can apply for jobs.')
        return redirect('jobs:job_detail', job_id=job_id)
    if Application.objects.filter(job=job, caregiver=request.user).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('jobs:job_detail', job_id=job_id)
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        resume = request.FILES.get('resume')
        credentials = request.FILES.get('credentials')
        reference_letter = request.FILES.get('reference_letter')
        app = Application.objects.create(
            job=job,
            caregiver=request.user,
            cover_letter=cover_letter,
            resume=resume,
            credentials=credentials,
            reference_letter=reference_letter
        )
        # Notify job creator
        notify_user(
            job.posted_by,
            'New Application for Your Job',
            f'Caregiver {request.user.get_full_name()} ({request.user.email}) has applied for your job "{job.title}".',
            job_id=job.id,
            request=request
        )
        messages.success(request, 'Applied for job. The job creator has been notified.')
        return redirect('jobs:job_detail', job_id=job_id)
    return render(request, 'jobs/apply_job.html', {'job': job})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    from jobs.models import Application
    can_apply = False
    already_applied = False
    application = None
    applicants = []
    if request.user.role == 'caregiver':
        already_applied = Application.objects.filter(job=job, caregiver=request.user).exists()
        can_apply = not already_applied
        if already_applied:
            application = Application.objects.get(job=job, caregiver=request.user)
    elif request.user == job.posted_by:
        applicants = Application.objects.filter(job=job)
    return render(request, 'custom_admin/job_detail.html', {
        'job': job,
        'can_apply': can_apply,
        'already_applied': already_applied,
        'application': application,
        'applicants': applicants
    })

@login_required
def update_application_status(request, application_id, status):
    from jobs.models import Application
    # Ensure only core.models.Notification is used

    app = get_object_or_404(Application, id=application_id)
    if request.user != app.job.posted_by:
        messages.error(request, 'Permission denied.')
        return redirect('custom_admin:job_detail', job_id=app.job.id)
    app.status = status
    app.save()
    notify_user(
        app.caregiver,
        f'Your Application for {app.job.title} has been {status.title()}',
        f'Your application status for the job "{app.job.title}" is now {status.title()}.',
        job_id=app.job.id,
        request=request
    )
    messages.success(request, f'Application marked as {status.title()} and caregiver notified.')
    return redirect('custom_admin:job_detail', job_id=app.job.id)


@login_required
def job_edit(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    if not is_custom_admin_or_family(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('custom_admin:job_list')
    if request.method == 'POST':
        job.title = request.POST.get('title')
        job.description = request.POST.get('description')
        job.schedule = request.POST.get('schedule')
        job.location = request.POST.get('location')
        job.pay = request.POST.get('pay')
        job.save()
        messages.success(request, 'Job updated successfully.')
        return redirect('custom_admin:job_list')
    return render(request, 'custom_admin/job_form.html', {'action': 'edit', 'job': job})

@login_required
def job_delete(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    from core.models import Notification
    if not is_custom_admin_or_family(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('custom_admin:job_list')
    if request.method == 'POST':
        # Delete related notifications (for all users) that link to this job
        job_url_pattern = f'/jobs/{job_id}/detail/'
        Notification.objects.filter(url__contains=job_url_pattern).delete()
        job.delete()
        messages.success(request, 'Job deleted successfully and related notifications cleaned up.')
        return redirect('custom_admin:job_list')
    return render(request, 'custom_admin/job_confirm_delete.html', {'job': job})

@login_required
@user_passes_test(is_admin)
def integration_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        integration = Integration(name=name)
        integration.save()
        return JsonResponse({'id': integration.id, 'name': integration.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_admin)
def integration_edit(request, integration_id):
    integration = Integration.objects.get(id=integration_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        integration.name = name
        integration.save()
        return JsonResponse({'id': integration.id, 'name': integration.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@user_passes_test(is_admin)
def integration_delete(request, integration_id):
    integration = Integration.objects.get(id=integration_id)
    integration.delete()
    return JsonResponse({'success': True})

@login_required
@user_passes_test(is_admin)
def integration_connect(request, integration_id):
    integration = Integration.objects.get(id=integration_id)
    # Logic to connect the integration goes here
    return JsonResponse({'success': True})

# --- Guide CRUD ---
@login_required
@user_passes_test(is_admin)
def guide_list(request):
    guides = Guide.objects.all().order_by('-published_at')
    return render(request, 'custom_admin/guide_list.html', {'guides': guides})

@login_required
@user_passes_test(is_admin)
def guide_add(request):
    if request.method == 'POST':
        form = GuideForm(request.POST)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.published_by = request.user
            guide.save()
            messages.success(request, 'Guide added successfully.')
            return redirect('custom_admin:guide_list')
    else:
        form = GuideForm()
    return render(request, 'custom_admin/guide_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def guide_edit(request, guide_id):
    guide = get_object_or_404(Guide, id=guide_id)
    if request.method == 'POST':
        form = GuideForm(request.POST, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guide updated successfully.')
            return redirect('custom_admin:guide_list')
    else:
        form = GuideForm(instance=guide)
    return render(request, 'custom_admin/guide_edit.html', {'form': form, 'guide': guide})

@login_required
@user_passes_test(is_admin)
def guide_delete(request, guide_id):
    guide = get_object_or_404(Guide, id=guide_id)
    if request.method == 'POST':
        guide.delete()
        messages.success(request, 'Guide deleted successfully.')
        return redirect('custom_admin:guide_list')
    return render(request, 'custom_admin/confirm_delete_guide.html', {'object': guide, 'type': 'Guide'})

# --- FAQ CRUD ---
@login_required
@user_passes_test(is_admin)
def faq_list(request):
    faqs = FAQ.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/faq_list.html', {'faqs': faqs})

@login_required
@user_passes_test(is_admin)
def faq_add(request):
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ added successfully.')
            return redirect('custom_admin:faq_list')
    else:
        form = FAQForm()
    return render(request, 'custom_admin/faq_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def faq_edit(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ updated successfully.')
            return redirect('custom_admin:faq_list')
    else:
        form = FAQForm(instance=faq)
    return render(request, 'custom_admin/faq_edit.html', {'form': form, 'faq': faq})

@login_required
@user_passes_test(is_admin)
def faq_delete(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        faq.delete()
        messages.success(request, 'FAQ deleted successfully.')
        return redirect('custom_admin:faq_list')
    return render(request, 'custom_admin/confirm_delete_faq.html', {'object': faq, 'type': 'FAQ'})

# --- Health Check Helper Functions ---
def check_database_health():
    try:
        from django.db import connection
        connection.ensure_connection()
        # You could also run a very simple query here, e.g., User.objects.exists()
        return "Healthy"
    except Exception:
        return "Error"

def check_storage_health():
    # Basic check for local media storage. Adapt if using cloud storage.
    try:
        from django.conf import settings
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            return "Not Configured"
        if not os.path.exists(media_root):
            return "Warning"  # Configured but path doesn't exist
        if not os.path.isdir(media_root):
            return "Warning"  # Path exists but is not a directory
        # Basic check passed if MEDIA_ROOT is a valid directory
        # More advanced: check writability or disk space (e.g., shutil.disk_usage)
        return "Healthy"
    except Exception:
        return "Error"

def check_background_jobs_health():
    # Placeholder: Highly dependent on the specific background task system (Celery, Django-Q, etc.)
    # Example for Celery (requires Celery app instance and celery library):
    # try:
    #     from celery.task.control import inspect
    #     celery_inspect = inspect()
    #     stats = celery_inspect.stats()
    #     if not stats: # No running workers
    #         return "Warning"
    #     return "Healthy"
    # except ImportError:
    #     return "Not Configured" # Celery not installed
    # except IOError: # Broker connection error
    #     return "Error"
    # except Exception:
    #     return "Error"
    return "Unknown" # Default status

@login_required
@user_passes_test(is_admin)
def maintenance_management(request):
    health_status = {
        'database': check_database_health(),
        'storage': check_storage_health(),
        'background_jobs': check_background_jobs_health()
    }
    context = {
        'health_status': health_status
    }
    return render(request, 'custom_admin/maintenance_management.html', context)

@login_required
@user_passes_test(is_admin)
def api_get_health_status(request):
    health_data = {
        'database_status': check_database_health(),
        'storage_status': check_storage_health(),
        'jobs_status': check_background_jobs_health(),
    }
    return JsonResponse(health_data)

@login_required
def stop_impersonation(request):
    orig_id = request.session.pop('impersonate_original_id', None)
    User = get_user_model()
    if orig_id:
        try:
            orig_user = User.objects.get(id=orig_id)
            login(request, orig_user)
            messages.info(request, "You have stopped impersonating and are now yourself again.")
            AuditLog.objects.create(
                user=orig_user,
                action='edit',
                target_type='user',
                target_id=request.user.id,
                target_repr=request.user.username,
                details=f"Admin {orig_user.username} stopped impersonating user {request.user.username} (ID {request.user.id})"
            )
        except User.DoesNotExist:
            logout(request)
            messages.warning(request, "Original admin user not found. Please log in again.")
    else:
        logout(request)
        messages.warning(request, "Impersonation session not found. Please log in again.")
    return redirect('custom_admin:user_management')

@login_required
@user_passes_test(is_admin)
def impersonate_user(request, user_id):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "You do not have permission to impersonate users.")
        return redirect('custom_admin:user_management')
    try:
        target_user = User.objects.get(id=user_id)
        request.session['impersonate_original_id'] = request.user.id
        login(request, target_user)
        messages.info(request, f"You are now impersonating {target_user.get_full_name() or target_user.username}.")
        AuditLog.objects.create(
            user=request.user,
            action='edit',
            target_type='user',
            target_id=target_user.id,
            target_repr=target_user.username,
            details=f"Admin {request.user.username} impersonated user {target_user.username} (ID {target_user.id})"
        )
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    return redirect('landing')
