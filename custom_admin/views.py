from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.apps import apps
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from .utils import get_app_models_data, get_model_filters, filter_queryset
from .forms import get_model_form
from accounts.models import AccountDeletionRequest
from accounts.forms import CustomAuthenticationForm

import csv
from django.http import HttpResponse
from chatbot.models import ChatbotLog
from feedback.models import Feedback, Rating
from accounts.models import AccountDeletionRequest

def is_staff(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff)
def export_logs(request):
    """
    Export logs as CSV for admin download. Supports multiple log types.
    Use ?type=chatbot|feedback|rating|account_deletion in the query string.
    """
    log_type = request.GET.get('type', 'chatbot')
    response = HttpResponse(content_type='text/csv')

    if log_type == 'feedback':
        response['Content-Disposition'] = 'attachment; filename="feedback_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Message', 'Created At', 'Is Moderated'])
        for fb in Feedback.objects.select_related('user').all():
            writer.writerow([
                fb.id,
                fb.user.username if fb.user else '',
                fb.message,
                fb.created_at.strftime('%Y-%m-%d %H:%M'),
                fb.is_moderated
            ])
    elif log_type == 'rating':
        response['Content-Disposition'] = 'attachment; filename="rating_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Caregiver', 'Reviewer', 'Stars', 'Review Text', 'Is Anonymous', 'Is Hidden', 'Created At', 'Admin Response'])
        for r in Rating.objects.select_related('caregiver', 'reviewer').all():
            writer.writerow([
                r.id,
                r.caregiver.username if r.caregiver else '',
                r.reviewer.username if r.reviewer else '',
                r.stars,
                r.review_text,
                r.is_anonymous,
                r.is_hidden,
                r.created_at.strftime('%Y-%m-%d %H:%M'),
                r.admin_response
            ])
    elif log_type == 'account_deletion':
        response['Content-Disposition'] = 'attachment; filename="account_deletion_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Requested At', 'Approved', 'Processed At'])
        for req in AccountDeletionRequest.objects.select_related('user').all():
            writer.writerow([
                req.id,
                req.user.username if req.user else '',
                req.requested_at.strftime('%Y-%m-%d %H:%M'),
                req.approved,
                req.processed_at.strftime('%Y-%m-%d %H:%M') if req.processed_at else ''
            ])
    else:
        # Default to chatbot logs
        response['Content-Disposition'] = 'attachment; filename="chatbot_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Timestamp', 'User Message', 'Bot Response', 'Reviewed By Admin'])
        for log in ChatbotLog.objects.select_related('user').all():
            writer.writerow([
                log.id,
                log.user.username if log.user else '',
                log.timestamp.strftime('%Y-%m-%d %H:%M'),
                log.user_message,
                log.bot_response,
                log.reviewed_by_admin,
            ])
    return response


class AdminLoginForm(CustomAuthenticationForm):
    def confirm_login_allowed(self, user):
        # Only allow users with role == 'admin' (not just is_staff/superuser)
        if not hasattr(user, 'role') or not (hasattr(user, 'is_admin_role') and user.is_admin_role()):
            from django.core.exceptions import ValidationError
            raise ValidationError(
                "Only admin credentials are allowed on this page.",
                code='invalid_login',
            )

class AdminLoginView(LoginView):
    form_class = AdminLoginForm
    template_name = 'custom_admin/admin_login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('custom_admin:admin_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin_login'] = True
        return context

admin_login = AdminLoginView.as_view()


def admin_logout(request):
    """
    Custom logout view that accepts both GET and POST requests.
    This is more convenient for admin interface links.
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:logout')


@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    app_list = get_app_models_data()
    
    # Add item counts for badges
    for app in app_list:
        for model in app['models']:
            model_class = apps.get_model(app['label'], model['name'])
            model['count'] = model_class.objects.count()
    
    # Existing context setup
    user_count = 0
    job_count = 0
    feedback_count = 0
    recent_activities = []
    
    # Determine if we're on the activity page
    is_activity_page = request.resolver_match.url_name == 'recent_activity'

    # Recent users
    try:
        User = apps.get_model('accounts', 'User')
        user_count = User.objects.count()
        recent_users = User.objects.order_by('-date_joined')[:5]
        for u in recent_users:
            recent_activities.append(f'User registered: {u.username} ({u.get_role_display()}) on {u.date_joined.strftime("%Y-%m-%d %H:%M")}')
    except Exception:
        pass

    # Recent jobs
    try:
        Job = apps.get_model('jobs', 'Job')
        job_count = Job.objects.count()
        recent_jobs = Job.objects.order_by('-created_at')[:5]
        for j in recent_jobs:
            recent_activities.append(f'Job posted: {j.title} by {getattr(j.posted_by, "username", "Unknown")} on {j.created_at.strftime("%Y-%m-%d %H:%M")}')
    except Exception:
        pass

    # Recent feedback
    try:
        Feedback = apps.get_model('feedback', 'Feedback')
        feedback_count = Feedback.objects.count()
        recent_feedbacks = Feedback.objects.order_by('-created_at')[:5]
        for f in recent_feedbacks:
            recent_activities.append(f'Feedback from {getattr(f.user, "username", "Unknown")} on {f.created_at.strftime("%Y-%m-%d %H:%M")}')
    except Exception:
        pass

    # Recent contact messages
    try:
        ContactMessage = apps.get_model('custom_admin', 'ContactMessage')
        recent_msgs = ContactMessage.objects.order_by('-created_at')[:5]
        for m in recent_msgs:
            recent_activities.append(f'Contact message from {m.name} on {m.created_at.strftime("%Y-%m-%d %H:%M")}')
    except Exception:
        pass

    # Sort all activities by date (extract date from string if possible)
    import re
    from datetime import datetime
    def extract_date(s):
        match = re.search(r'on (\d{4}-\d{2}-\d{2} \d{2}:\d{2})', s)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")
            except Exception:
                pass
        return datetime.min
    recent_activities.sort(key=extract_date, reverse=True)
    recent_activities = recent_activities[:8]  # Show top 8 most recent

            
    # Notification badge counts
    try:
        ContactMessage = apps.get_model('custom_admin', 'ContactMessage')
        unread_contact_count = ContactMessage.objects.filter(is_read=False).count()
    except LookupError:
        unread_contact_count = 0
    try:
        Feedback = apps.get_model('feedback', 'Feedback')
        unmoderated_feedback_count = Feedback.objects.filter(is_moderated=False).count()
    except LookupError:
        unmoderated_feedback_count = 0

    # Add pending account deletion requests
    try:
        pending_deletion_count = AccountDeletionRequest.objects.filter(approved=False).count()
        pending_deletions = AccountDeletionRequest.objects.filter(approved=False).select_related('user')[:5]
    except Exception:
        pending_deletion_count = 0
        pending_deletions = []

    context = {
        'apps': app_list,
        'user_count': user_count,
        'job_count': job_count,
        'feedback_count': feedback_count,
        'recent_activities': recent_activities,
        'unread_contact_count': unread_contact_count,
        'unmoderated_feedback_count': unmoderated_feedback_count,
        'pending_deletion_count': pending_deletion_count,
        'pending_deletions': pending_deletions,
    }
    
    # Use different template based on URL pattern
    template = 'custom_admin/recent_activity.html' if is_activity_page else 'custom_admin/admin_index.html'
    return render(request, template, context)


@login_required
@user_passes_test(is_staff)
def admin_list(request, app_label, model_name):
    # Get app data for sidebar
    apps_data = get_app_models_data()
    
    model = apps.get_model(app_label, model_name)
    objects = model.objects.all()
    
    # Get model fields for display
    fields = [field.name for field in model._meta.fields if field.name != 'id']
    
    # Build filter options
    filters = get_model_filters(model)
    
    # Apply filters and search
    objects = filter_queryset(model, objects, request.GET)
    
    # Get search query for template context
    search_query = request.GET.get('search', '')
    
    # Notification badge counts
    try:
        ContactMessage = apps.get_model('custom_admin', 'ContactMessage')
        unread_contact_count = ContactMessage.objects.filter(is_read=False).count()
    except LookupError:
        unread_contact_count = 0
    try:
        Feedback = apps.get_model('feedback', 'Feedback')
        unmoderated_feedback_count = Feedback.objects.filter(is_moderated=False).count()
    except LookupError:
        unmoderated_feedback_count = 0

    return render(request, 'custom_admin/admin_list_filters.html', {
        'objects': objects,
        'fields': fields,
        'model_name': model._meta.verbose_name,
        'app_label': app_label,
        'model_name': model.__name__,
        'add_url': reverse('custom_admin:admin_add', args=[app_label, model_name]),
        'filters': filters,
        'search_query': search_query,
        'apps': apps_data,  # Add apps data for sidebar
        'unread_contact_count': unread_contact_count,
        'unmoderated_feedback_count': unmoderated_feedback_count
    })

@login_required
@user_passes_test(is_staff)
def admin_add(request, app_label, model_name):
    # Get app data for sidebar
    apps_data = get_app_models_data()
    
    model = apps.get_model(app_label, model_name)
    ModelForm = get_model_form(app_label, model_name)
    
    if request.method == 'POST':
        form = ModelForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f'{model._meta.verbose_name} was created successfully')
            return redirect('custom_admin:admin_list', app_label=app_label, model_name=model_name)
    else:
        form = ModelForm()
        
    return render(request, 'custom_admin/admin_form.html', {
        'form': form,
        'form_title': f'Add {model._meta.verbose_name}',
        'list_url': reverse('custom_admin:admin_list', args=[app_label, model_name]),
        'apps': apps_data,  # Add apps data for sidebar
        'app_label': app_label,
        'model_name': model_name
    })

@login_required
@user_passes_test(is_staff)
def admin_edit(request, app_label, model_name, pk):
    # Get app data for sidebar
    apps_data = get_app_models_data()
    
    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)
    ModelForm = get_model_form(app_label, model_name)
    
    if request.method == 'POST':
        form = ModelForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'{model._meta.verbose_name} was updated successfully')
            return redirect('custom_admin:admin_list', app_label=app_label, model_name=model_name)
    else:
        form = ModelForm(instance=obj)
        
    return render(request, 'custom_admin/admin_form.html', {
        'form': form,
        'form_title': f'Edit {model._meta.verbose_name}',
        'list_url': reverse('custom_admin:admin_list', args=[app_label, model_name]),
        'object': obj,
        'apps': apps_data,  # Add apps data for sidebar
        'app_label': app_label,
        'model_name': model_name
    })

@login_required
@user_passes_test(is_staff)
def admin_delete(request, app_label, model_name, pk):
    # Get app data for sidebar
    apps_data = get_app_models_data()
    
    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, f'{model._meta.verbose_name} was deleted successfully')
        return redirect('custom_admin:admin_list', app_label=app_label, model_name=model_name)
    return render(request, 'custom_admin/admin_confirm_delete.html', {
        'model_name': model._meta.verbose_name,
        'object': obj,
        'list_url': reverse('custom_admin:admin_list', args=[app_label, model_name]),
        'apps': apps_data,  # Add apps data for sidebar
        'app_label': app_label,
        'model_name': model_name
    })

@login_required
@user_passes_test(is_staff)
def admin_bulk_delete(request, app_label, model_name):
    # Get app data for sidebar (in case we need to render an error page)
    apps_data = get_app_models_data()
    
    if request.method == 'POST':
        model = apps.get_model(app_label, model_name)
        selected_ids = request.POST.getlist('selected_ids')
        if selected_ids:
            objects = model.objects.filter(pk__in=selected_ids)
            count = objects.count()
            objects.delete()
            messages.success(request, f'{count} {model._meta.verbose_name_plural} were deleted successfully')
        return redirect('custom_admin:admin_list', app_label=app_label, model_name=model_name)
    # If not POST, redirect to list view which already has the apps data
    return redirect('custom_admin:admin_list', app_label=app_label, model_name=model_name)

@login_required
@user_passes_test(is_staff)
def admin_view(request, app_label, model_name, pk):
    apps_data = get_app_models_data()
    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)

    # Auto-mark as read/moderated if ContactMessage or Feedback
    if app_label == 'custom_admin' and model_name == 'ContactMessage' and not obj.is_read:
        obj.is_read = True
        obj.save(update_fields=['is_read'])
    if app_label == 'feedback' and model_name == 'Feedback' and hasattr(obj, 'is_moderated') and not obj.is_moderated:
        obj.is_moderated = True
        obj.save(update_fields=['is_moderated'])
    # Collect fields except password
    fields = {}
    for field in model._meta.fields:
        if field.name != 'password':
            fields[field.verbose_name.title() if hasattr(field, 'verbose_name') else field.name.title()] = getattr(obj, field.name)
    # Verification logic for caregivers only
    can_verify = False
    is_verified = False
    if hasattr(obj, 'is_verified') and hasattr(obj, 'is_caregiver') and callable(getattr(obj, 'is_caregiver')):
        if obj.is_caregiver():
            can_verify = True
            is_verified = getattr(obj, 'is_verified', False)
            if request.method == 'POST' and not is_verified and request.POST.get('verify'):
                obj.is_verified = True
                obj.save()
                messages.success(request, f'{model._meta.verbose_name} has been verified.')
                return redirect('custom_admin:admin_view', app_label=app_label, model_name=model_name, pk=pk)
    return render(request, 'custom_admin/admin_view.html', {
        'fields': fields,
        'object': obj,
        'model_name': model._meta.verbose_name.title(),
        'is_verified': is_verified,
        'can_verify': can_verify,
        'list_url': reverse('custom_admin:admin_list', args=[app_label, model_name]),
        'apps': apps_data,
        'app_label': app_label,
        'model_name': model_name,
    })
