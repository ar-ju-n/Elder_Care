from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.conf import settings
from accounts.models import User

User = get_user_model()

class SavedSearch(models.Model):
    SEARCH_TYPES = [
        ('job', 'Job Search'),
        ('caregiver', 'Caregiver Search'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_searches'
    )
    name = models.CharField(max_length=100)
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    query_params = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Saved Searches'
    
    def __str__(self):
        return f"{self.name} - {self.get_search_type_display()}"


class JobQuerySet(models.QuerySet):
    def active(self):
        return self.filter(approved=True, status=Job.STATUS_OPEN)
    
    def for_user(self, user):
        if user.is_authenticated and user.is_family():
            return self.filter(posted_by=user)
        elif user.is_authenticated and user.is_admin_role():
            return self.all()
        return self.filter(approved=True)
    
    def with_filters(self, filters):
        queryset = self
        
        # Text search
        if search_query := filters.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Location filter
        if location := filters.get('location'):
            queryset = queryset.filter(location__icontains=location)
            
        # Pay filter
        if pay := filters.get('pay'):
            if pay.isdigit():
                queryset = queryset.filter(pay__gte=float(pay))
                
        # Status filter
        if status := filters.get('status'):
            queryset = queryset.filter(status=status)
            
        # Date range filter
        if start_date := filters.get('start_date'):
            queryset = queryset.filter(created_at__date__gte=start_date)
            
        if end_date := filters.get('end_date'):
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        # Ordering
        order_by = filters.get('order_by', '-created_at')
        if order_by.lstrip('-') in ['created_at', 'pay', 'title']:
            queryset = queryset.order_by(order_by)
            
        return queryset


class Job(models.Model):
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    schedule = models.CharField(max_length=255)
    location = models.CharField(max_length=255, db_index=True)
    pay = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs', db_index=True)
    assigned_caregiver = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='assigned_jobs', 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'caregiver'},
        db_index=True
    )
    approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_seen = models.BooleanField(default=False)
    
    objects = JobQuerySet.as_manager()
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at'], name='created_at_desc_idx'),
            models.Index(fields=['pay'], name='pay_idx'),
            models.Index(fields=['location'], name='location_idx'),
        ]
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.status == self.STATUS_COMPLETED and not self.assigned_caregiver:
            raise ValueError("Cannot mark job as completed without an assigned caregiver")
        super().save(*args, **kwargs)
        
        # Send notification if status changed
        if 'update_fields' in kwargs and 'status' in kwargs['update_fields']:
            self._notify_status_change()
    
    def _notify_status_change(self):
        from django_htmx.http import trigger_client_event
        from django.template.loader import render_to_string
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        group_name = f'job_{self.id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'job_status_update',
                'job_id': self.id,
                'status': self.get_status_display(),
                'message': f'Job status updated to: {self.get_status_display()}'
            }
        )
    
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
