from django.db import models
from accounts.models import User

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    schedule = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    pay = models.DecimalField(max_digits=10, decimal_places=2)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    assigned_caregiver = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='assigned_jobs', null=True, blank=True, limit_choices_to={'role': 'caregiver'})
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    caregiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', limit_choices_to={'role': 'caregiver'})
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, help_text='Upload your resume (PDF or Word document)')
    credentials = models.FileField(upload_to='credentials/', blank=True, null=True, help_text='Upload your certifications or credentials (PDF format)')
    reference_letter = models.FileField(upload_to='references/', blank=True, null=True, help_text='Upload reference letters if available')
    status = models.CharField(max_length=20, choices=[('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')], default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'caregiver')

    def __str__(self):
        return f"{self.caregiver} -> {self.job}"
