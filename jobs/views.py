from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
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
    jobs = Job.objects.filter(approved=True)
    template = 'jobs/job_list.html'
    context = {'jobs': jobs}
    
    # Customize view based on user role
    if request.user.is_authenticated:
        if request.user.is_elderly():
            template = 'jobs/find_caregiver.html'
            # Only show verified caregivers
            verified_caregivers = User.objects.filter(role='caregiver', is_verified=True)
            context['caregivers'] = verified_caregivers
            context['title'] = 'Find a Caregiver'
            context['button_text'] = 'Contact Caregiver'
        elif request.user.is_caregiver():
            context['title'] = 'Available Jobs'
            context['button_text'] = 'Apply'
        elif request.user.is_family():
            context['title'] = 'Post Caregiving Jobs'
            context['button_text'] = 'Post a Job'
    
    return render(request, template, context)

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    already_applied = False
    applications = None
    user_application = None
    
    # For caregivers, check if they've already applied
    if request.user.is_caregiver():
        user_application = Application.objects.filter(job=job, caregiver=request.user).first()
        already_applied = user_application is not None
    
    # For employers (family members) and admins, show all applications
    if request.user.is_family() and job.posted_by == request.user or request.user.is_admin_role():
        applications = Application.objects.filter(job=job).select_related('caregiver')
    
    context = {
        'job': job,
        'already_applied': already_applied,
        'applications': applications,
        'user_application': user_application
    }
    
    return render(request, 'jobs/job_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_family() or u.is_admin_role())
def post_job_view(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = post_job(**form.cleaned_data, posted_by=request.user)
            messages.success(request, 'Job posted. Awaiting admin approval.')
            return redirect('jobs:job_list')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})

@login_required
@user_passes_test(is_caregiver)
def apply_job_view(request, job_id):
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
    caregivers = User.objects.filter(role='caregiver')
    if request.method == 'POST':
        caregiver_id = request.POST.get('caregiver_id')
        caregiver = get_object_or_404(User, id=caregiver_id, role='caregiver')
        assign_caregiver(job, caregiver)
        messages.success(request, f'Caregiver {caregiver.username} assigned to job {job.title}.')
        return redirect('jobs:job_detail', job_id=job.id)
    return render(request, 'jobs/assign_caregiver.html', {'job': job, 'caregivers': caregivers})
