from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.apps import apps
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from .utils import get_app_models_data, get_model_filters, filter_queryset
from .forms import get_model_form

def is_staff(user):
    return user.is_staff or user.is_superuser


class AdminLoginView(LoginView):
    template_name = 'custom_admin/admin_login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('custom_admin:admin_dashboard')


admin_login = AdminLoginView.as_view()


def admin_logout(request):
    """
    Custom logout view that accepts both GET and POST requests.
    This is more convenient for admin interface links.
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('custom_admin:admin_login')


@login_required
@user_passes_test(is_staff)
def admin_dashboard(request):
    app_list = get_app_models_data()
    
    # Get statistics for the dashboard
    user_count = 0
    job_count = 0
    feedback_count = 0
    recent_activities = []
    
    # Try to get User model count
    try:
        User = apps.get_model('accounts', 'User')
        user_count = User.objects.count()
    except LookupError:
        pass
    
    # Try to get Job model count
    try:
        Job = apps.get_model('jobs', 'Job')
        job_count = Job.objects.count()
    except LookupError:
        pass
    
    # Try to get Feedback model count
    try:
        Feedback = apps.get_model('feedback', 'Feedback')
        feedback_count = Feedback.objects.count()
        
        # Get recent feedback for activity
        recent_feedbacks = Feedback.objects.order_by('-created_at')[:5]
        for feedback in recent_feedbacks:
            recent_activities.append(f'New feedback from {feedback.user} on {feedback.created_at.strftime("%Y-%m-%d")}')
    except (LookupError, AttributeError):
        pass
            
    return render(request, 'custom_admin/admin_index.html', {
        'apps': app_list,
        'user_count': user_count,
        'job_count': job_count,
        'feedback_count': feedback_count,
        'recent_activities': recent_activities
    })


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
    
    return render(request, 'custom_admin/admin_list_filters.html', {
        'objects': objects,
        'fields': fields,
        'model_name': model._meta.verbose_name,
        'app_label': app_label,
        'model_name': model.__name__,
        'add_url': reverse('custom_admin:admin_add', args=[app_label, model_name]),
        'filters': filters,
        'search_query': search_query,
        'apps': apps_data  # Add apps data for sidebar
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
