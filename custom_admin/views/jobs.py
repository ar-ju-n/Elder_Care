"""
Job Management Views for Custom Admin
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from jobs.models import Job, Application
from jobs.forms import JobForm, ApplicationForm as JobApplicationForm
from accounts.models import User

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def job_list(request):
    """List all jobs with filtering options"""
    jobs = Job.objects.all().order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        jobs = jobs.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    context = {
        'jobs': jobs,
        'status_choices': dict(Job.STATUS_CHOICES),
        'active_status': status,
        'search_query': search or '',
        'active_tab': 'jobs',
    }
    
    return render(request, 'custom_admin/jobs/job_list.html', context)

@login_required
@user_passes_test(is_admin)
def job_detail(request, job_id):
    """View details of a specific job posting"""
    job = get_object_or_404(Job, id=job_id)
    applications = job.applications.all().order_by('-applied_at')
    
    context = {
        'job': job,
        'applications': applications,
        'active_tab': 'jobs',
    }
    return render(request, 'custom_admin/jobs/job_detail.html', context)

@login_required
@user_passes_test(is_admin)
def job_create(request):
    """Create a new job posting"""
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Job posted successfully.')
            return redirect('custom_admin:job_list')
    else:
        form = JobForm()
    
    return render(request, 'custom_admin/jobs/job_form.html', {
        'form': form,
        'action': 'Post New',
        'active_tab': 'jobs',
    })

@login_required
@user_passes_test(is_admin)
def job_edit(request, job_id):
    """Edit an existing job posting"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('custom_admin:job_list')
    else:
        form = JobForm(instance=job)
    
    return render(request, 'custom_admin/jobs/job_form.html', {
        'form': form,
        'action': 'Edit',
        'job': job,
        'active_tab': 'jobs',
    })

@login_required
@user_passes_test(is_admin)
def job_delete(request, job_id):
    """Delete a job posting"""
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('custom_admin:job_list')
    
    return render(request, 'custom_admin/jobs/job_confirm_delete.html', {
        'job': job,
        'active_tab': 'jobs',
    })

@login_required
@user_passes_test(is_admin)
def job_applications(request, job_id=None):
    """List job applications with filtering options"""
    applications = Application.objects.select_related('job', 'caregiver').order_by('-applied_at')
    
    # Filter by job if job_id is provided
    if job_id:
        job = get_object_or_404(Job, id=job_id)
        applications = applications.filter(job=job)
    else:
        job = None
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        applications = applications.filter(
            Q(caregiver__first_name__icontains=search) |
            Q(caregiver__last_name__icontains=search) |
            Q(caregiver__email__icontains=search) |
            Q(cover_letter__icontains=search)
        )
    
    context = {
        'applications': applications,
        'job': job,
        'status_choices': dict(Application._meta.get_field('status').choices),
        'active_status': status,
        'search_query': search or '',
        'active_tab': 'jobs',
    }
    
    return render(request, 'custom_admin/jobs/application_list.html', context)

@login_required
@user_passes_test(is_admin)
def update_application_status(request, application_id, status):
    """Update the status of a job application"""
    application = get_object_or_404(Application, id=application_id)
    status_choices = dict(Application._meta.get_field('status').choices)
    
    if status in status_choices:
        old_status = application.status
        application.status = status
        application.save()
        
        # Log the status change
        messages.success(request, f'Application status updated to {status_choices[status]}.')
    
    job_id = request.GET.get('job_id')
    if job_id:
        return redirect('custom_admin:jobs:job_applications', job_id=job_id)
    else:
        return redirect('custom_admin:jobs:job_applications')

@login_required
@user_passes_test(is_admin)
def application_detail(request, application_id):
    """View details of a job application"""
    application = get_object_or_404(
        Application.objects.select_related('job', 'caregiver'),
        id=application_id
    )
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated successfully.')
            return redirect('custom_admin:application_detail', application_id=application.id)
    else:
        form = JobApplicationForm(instance=application)
    
    return render(request, 'custom_admin/jobs/application_detail.html', {
        'application': application,
        'form': form,
        'status_choices': dict(Application._meta.get_field('status').choices),
        'active_tab': 'jobs',
    })

@login_required
@user_passes_test(is_admin)
def apply_for_job(request, job_id):
    """
    Handle job application submission from admin interface
    """
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.status = 'pending'  # Or 'under_review' based on your workflow
            application.submitted_at = timezone.now()
            
            # If this is an admin applying on behalf of a user
            if 'user_id' in request.POST and request.POST['user_id']:
                try:
                    user = User.objects.get(id=request.POST['user_id'])
                    application.applicant = user
                except User.DoesNotExist:
                    messages.error(request, 'Invalid user selected.')
                    return redirect('custom_admin:job_detail', job_id=job.id)
            else:
                application.applicant = request.user
            
            application.save()
            
            # Handle any additional fields or files here
            if 'resume' in request.FILES:
                application.resume = request.FILES['resume']
                application.save()
            
            # Log the application
            AuditLog.objects.create(
                user=request.user,
                action='JOB_APPLICATION_CREATE',
                details=f'Submitted application for job: {job.title}',
                status='SUCCESS'
            )
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('custom_admin:job_detail', job_id=job.id)
    else:
        initial = {}
        # Pre-fill with user data if applying on behalf of someone
        if 'user_id' in request.GET:
            try:
                user = User.objects.get(id=request.GET['user_id'])
                initial = {
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'phone': user.phone if hasattr(user, 'phone') else '',
                    'user_id': user.id
                }
            except (User.DoesNotExist, ValueError):
                pass
        
        form = JobApplicationForm(initial=initial)
    
    context = {
        'form': form,
        'job': job,
        'active_tab': 'jobs',
    }
    
    return render(request, 'custom_admin/jobs/job_application_form.html', context)

@login_required
@user_passes_test(is_admin)
def job_analytics(request):
    """Job posting analytics and statistics"""
    # Total jobs counts
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(status='open').count()
    total_applications = Application.objects.count()
    
    # Applications by status
    applications_by_status = Application.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Jobs with most applications
    popular_jobs = Job.objects.annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:5]
    
    # Monthly applications trend (last 6 months)
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_applications = Application.objects.filter(
        applied_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('applied_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'applications_by_status': applications_by_status,
        'popular_jobs': popular_jobs,
        'monthly_applications': list(monthly_applications),
        'active_tab': 'jobs',
    }
    
    return render(request, 'custom_admin/jobs/job_analytics.html', context)
