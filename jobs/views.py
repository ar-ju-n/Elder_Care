from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, Http404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import AccessMixin
from django.utils.decorators import method_decorator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import Job, Application
from .forms import JobForm, ApplicationForm
from .services import post_job, apply_to_job, assign_caregiver
from accounts.models import User

# Helper role checks
def is_family(user):
    return user.is_authenticated and user.is_family()
def is_admin(user):
    return user.is_authenticated and user.is_admin_role()
def is_caregiver(user):
    return user.is_authenticated and user.is_caregiver()

def job_list(request):
    # Get filter parameters with defaults
    filters = {
        'search': request.GET.get('search', ''),
        'location': request.GET.get('location', ''),
        'pay': request.GET.get('pay', ''),
        'status': request.GET.get('status', ''),
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'order_by': request.GET.get('order_by', '-created_at'),
    }
    
    my_jobs = request.GET.get('my_jobs', '') == '1'
    my_applications = request.GET.get('my_applications', '') == '1'
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    
    # Base queryset with user-specific filtering
    jobs = Job.objects.for_user(request.user)
    
    # Apply additional filters
    if request.user.is_authenticated and request.user.is_caregiver and my_applications:
        applied_job_ids = Application.objects.filter(
            caregiver=request.user
        ).values_list('job_id', flat=True)
        jobs = jobs.filter(id__in=applied_job_ids)
    
    # Apply all filters from the form
    jobs = jobs.with_filters(filters)
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format in ['csv', 'pdf']:
        return export_jobs(jobs, export_format)
    
    # Pagination
    paginator = Paginator(jobs, 9)  # Show 9 jobs per page (3 per row)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)
    
    # For AJAX requests, return only the job items HTML
    if is_ajax:
        return render(request, 'jobs/partials/job_list_items.html', {
            'page_obj': page_obj,
            'user': request.user,
        })
    
    # Prepare context
    context = {
        'page_obj': page_obj,
        'filters': filters,
        'my_jobs': my_jobs,
        'my_applications': my_applications,
        'title': 'Available Jobs',
        'status_choices': Job.STATUS_CHOICES,
        'sort_options': [
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('-pay', 'Highest Pay'),
            ('pay', 'Lowest Pay'),
            ('title', 'Title (A-Z)'),
            ('-title', 'Title (Z-A)'),
        ],
    }
    
    # Set appropriate title based on user role and filters
    if request.user.is_authenticated:
        if request.user.is_family:
            context['title'] = 'My Job Posts' if my_jobs else 'Post Caregiving Jobs'
        elif request.user.is_caregiver:
            context['title'] = 'My Applications' if my_applications else 'Available Jobs'
    
    # Add saved searches if user is authenticated
    if request.user.is_authenticated:
        try:
            context['saved_searches'] = request.user.saved_searches.filter(
                search_type='job'
            ).order_by('-created_at')[:5]
        except AttributeError:
            # In case the saved_searches relationship doesn't exist yet
            context['saved_searches'] = []
    else:
        context['saved_searches'] = []
    
    return render(request, 'jobs/job_list.html', context)


def export_jobs(queryset, format='csv'):
    """Export jobs to CSV or PDF"""
    import csv
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    import io
    
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Description', 'Location', 'Pay', 'Status', 'Posted By', 'Created At'])
        
        for job in queryset:
            writer.writerow([
                job.title,
                job.description[:100] + '...' if len(job.description) > 100 else job.description,
                job.location,
                job.pay,
                job.get_status_display(),
                job.posted_by.get_full_name() or job.posted_by.email,
                job.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        return response
    
    elif format == 'pdf':
        template = get_template('jobs/export/job_list_pdf.html')
        context = {'jobs': queryset}
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="jobs_export.pdf"'
        
        # Create PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        
        return response
    
    return HttpResponse('Invalid export format', status=400)

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    
    # Check if user has permission to view this job
    if not job.approved and not (request.user.is_admin_role() or job.posted_by == request.user):
        if is_ajax:
            return JsonResponse({'error': 'You do not have permission to view this job.'}, status=403)
        messages.error(request, 'You do not have permission to view this job.')
        return redirect('jobs:job_list')
    
    # For caregivers, check if they've already applied
    user_application = None
    if request.user.is_caregiver:
        user_application = Application.objects.filter(job=job, caregiver=request.user).first()
    
    # For employers (family members) and admins, show all applications
    applications = None
    if (request.user.is_family and job.posted_by == request.user) or request.user.is_admin_role():
        applications = Application.objects.filter(job=job).select_related('caregiver')
    
    # Handle AJAX requests for job details
    if is_ajax:
        data = {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'location': job.location,
            'pay': str(job.pay),
            'schedule': job.schedule,
            'posted_by': {
                'id': job.posted_by.id,
                'name': job.posted_by.get_full_name() or job.posted_by.username,
                'is_current_user': job.posted_by == request.user
            },
            'created_at': job.created_at.isoformat(),
            'assigned_caregiver': {
                'id': job.assigned_caregiver.id,
                'name': job.assigned_caregiver.get_full_name() or job.assigned_caregiver.username
            } if job.assigned_caregiver else None,
            'user_application': {
                'id': user_application.id,
                'status': user_application.status,
                'applied_at': user_application.applied_at.isoformat()
            } if user_application else None,
            'can_apply': request.user.is_caregiver and not job.assigned_caregiver and not user_application,
            'can_manage': request.user == job.posted_by or request.user.is_admin_role()
        }
        return JsonResponse(data)
    
    context = {
        'job': job,
        'applications': applications,
        'user_application': user_application,
        'title': job.title,
        'can_apply': request.user.is_caregiver and not job.assigned_caregiver and not user_application,
        'can_manage': request.user == job.posted_by or request.user.is_admin_role()
    }
    
    return render(request, 'jobs/job_detail.html', context)

class JobCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    
    def test_func(self):
        return self.request.user.is_family() or self.request.user.is_admin_role()
    
    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Job posted successfully.' + 
                        (' It will be visible after admin approval.' if not self.request.user.is_admin_role() else ''))
        return response
    
    def get_success_url(self):
        return reverse_lazy('jobs:job_detail', kwargs={'job_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Post a New Job'
        return context


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    pk_url_kwarg = 'job_id'
    
    def test_func(self):
        job = self.get_object()
        return (self.request.user == job.posted_by) or self.request.user.is_admin_role()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Job updated successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('jobs:job_detail', kwargs={'job_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Job: {self.object.title}'
        return context


class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Job
    pk_url_kwarg = 'job_id'
    template_name = 'jobs/job_confirm_delete.html'
    
    def test_func(self):
        job = self.get_object()
        return (self.request.user == job.posted_by) or self.request.user.is_admin_role()
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Job has been deleted successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('jobs:job_list')

@login_required
def apply_job_view(request, job_id):
    if not request.user.is_verified_caregiver():
        messages.error(request, "Your caregiver account must be verified by an admin before you can apply for jobs.")
        return redirect('accounts:profile', user_id=request.user.id)

    job = get_object_or_404(Job, id=job_id, approved=True)
    if Application.objects.filter(job=job, caregiver=request.user).exists():
        messages.info(request, 'You have already applied to this job.')
        return redirect('jobs:job_detail', job_id=job.id)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create application but don't save yet
            application = form.save(commit=False)
            application.job = job
            application.caregiver = request.user
            application.save()
            
            messages.success(request, 'Application submitted successfully with your documents.')
            return redirect('jobs:job_detail', job_id=job.id)
    else:
        form = ApplicationForm()
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

@login_required
@user_passes_test(lambda u: u.is_family() or u.is_admin_role())
def update_application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    job = application.job
    
    # Ensure only the job poster or an admin can update the status
    if not (request.user.is_admin_role() or (request.user.is_family() and job.posted_by == request.user)):
        messages.error(request, 'You do not have permission to update this application.')
        return redirect('jobs:job_detail', job_id=job.id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['accepted', 'rejected']:
            application.status = new_status
            application.save()
            
            # If accepted, assign the caregiver to the job
            if new_status == 'accepted':
                job.assigned_caregiver = application.caregiver
                job.save()
                # Reject all other applications for this job
                Application.objects.filter(job=job).exclude(id=application.id).update(status='rejected')
                messages.success(request, f'Application from {application.caregiver.get_full_name()} has been accepted.')
            else:
                messages.info(request, f'Application from {application.caregiver.get_full_name()} has been rejected.')
        else:
            messages.error(request, 'Invalid status provided.')
    
    return redirect('jobs:job_detail', job_id=job.id)

@login_required
@user_passes_test(is_admin)
def admin_approve_jobs(request):
    jobs = Job.objects.filter(approved=False)
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        action = request.POST.get('action')
        job = get_object_or_404(Job, id=job_id)
        if action == 'approve':
            job.approved = True
            job.save()
            messages.success(request, f'Job {job.title} approved.')
        elif action == 'reject':
            job.delete()
            messages.success(request, f'Job {job.title} rejected and deleted.')
    return render(request, 'jobs/admin_approve_jobs.html', {'jobs': jobs})

@login_required
@user_passes_test(is_admin)
def assign_caregiver_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST' and (request.user == job.posted_by or request.user.is_admin_role()):
        caregiver_id = request.POST.get('caregiver_id')
        if caregiver_id:
            caregiver = get_object_or_404(User, id=caregiver_id, role='caregiver')
            assign_caregiver(job, caregiver)
            
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'job_{job.id}',
                {
                    'type': 'job_update',
                    'message': 'Job assigned',
                    'assigned_caregiver': {
                        'id': caregiver.id,
                        'name': caregiver.get_full_name() or caregiver.username,
                        'avatar': caregiver.profile_picture.url if hasattr(caregiver, 'profile_picture') and caregiver.profile_picture else None
                    }
                }
            )
            
            messages.success(request, f'Successfully assigned {caregiver.get_full_name()} to this job.')
    return redirect('jobs:job_detail', job_id=job.id)

@login_required
@require_http_methods(['POST'])
def update_job_status(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user has permission to update job status
    if not (request.user == job.posted_by or request.user.is_admin_role()):
        return JsonResponse({'error': 'You do not have permission to update this job.'}, status=403)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Job.STATUS_CHOICES):
            old_status = job.status
            job.status = new_status
            job.save()
            
            # Notify via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'job_{job_id}',
                {
                    'type': 'status_update',
                    'status': job.get_status_display(),
                    'job_id': job_id
                }
            )
            
            # Send notification to assigned caregiver if status changes to 'in_progress'
            if new_status == 'in_progress' and job.assigned_caregiver:
                # You can add notification logic here
                pass
                
            messages.success(request, f'Job status updated to {job.get_status_display()}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'new_status': job.status,
                    'new_status_display': job.get_status_display(),
                    'message': f'Job status updated to {job.get_status_display()}'
                })
    
    return redirect('jobs:job_detail', job_id=job_id)


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = 'jobs/application_detail.html'
    context_object_name = 'application'
    pk_url_kwarg = 'application_id'
    
    def get_queryset(self):
        # Only allow the job poster, admin, or the applicant to view the application
        queryset = super().get_queryset().select_related('job', 'caregiver', 'caregiver__userprofile')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        user = self.request.user
        
        # Check if user has permission to view this application
        if not (user == application.caregiver or user == application.job.posted_by or user.is_admin_role()):
            raise Http404("You don't have permission to view this application.")
        
        # Add additional context
        context['title'] = f'Application for {application.job.title}'
        context['can_manage'] = user == application.job.posted_by or user.is_admin_role()
        
        return context


def delete_application(request, application_id):
    """
    Delete an application. Only the job poster or admin can delete an application.
    """
    application = get_object_or_404(Application, id=application_id)
    job_id = application.job.id
    
    # Check permissions
    if not (request.user == application.job.posted_by or request.user.is_admin_role()):
        messages.error(request, 'You do not have permission to delete this application.')
        return redirect('jobs:job_detail', job_id=job_id)
    
    if request.method == 'POST':
        # Delete the application
        application.delete()
        messages.success(request, 'Application has been deleted successfully.')
        return redirect('jobs:job_detail', job_id=job_id)
    
    # If not a POST request, redirect to job detail
    return redirect('jobs:job_detail', job_id=job_id)
