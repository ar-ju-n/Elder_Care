"""
Business logic for jobs: posting, filtering, applying, admin assignment, etc.
"""
from .models import Job, Application
from accounts.models import User

def post_job(**kwargs):
    return Job.objects.create(**kwargs)

def apply_to_job(job, caregiver, cover_letter=None):
    return Application.objects.create(job=job, caregiver=caregiver, cover_letter=cover_letter)

def assign_caregiver(job, caregiver):
    job.assigned_caregiver = caregiver
    job.save()
    return job
