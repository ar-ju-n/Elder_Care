from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Role choices
    ELDERLY = 'elderly'
    CAREGIVER = 'caregiver'
    FAMILY = 'family'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ELDERLY, 'Elderly'),
        (CAREGIVER, 'Caregiver'),
        (FAMILY, 'Family Member'),
        (ADMIN, 'Administrator'),
    ]
    
    # Language choices
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ne', 'Nepali'),
        ('hi', 'Hindi'),
    ]
    
    # Timezone choices
    TIMEZONE_CHOICES = [
        ('UTC', 'UTC'),
        ('Asia/Kathmandu', 'Nepal Time'),
        ('Asia/Kolkata', 'India Time'),
        ('US/Eastern', 'US Eastern Time'),
        ('US/Pacific', 'US Pacific Time'),
        ('Europe/London', 'UK Time'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ELDERLY)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    # Settings fields
    email_notifications = models.BooleanField(default=True)
    language_preference = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')
    
    # Verification field for caregivers
    is_verified = models.BooleanField(default=False, help_text="Designates whether this caregiver has been verified by an admin.")
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Additional methods to check roles
    def is_elderly(self):
        return self.role == self.ELDERLY
    
    def is_caregiver(self):
        return self.role == self.CAREGIVER
    
    def is_family(self):
        return self.role == self.FAMILY
    
    def is_admin_role(self):
        return self.role == self.ADMIN
        
    def is_verified_caregiver(self):
        return self.is_caregiver() and self.is_verified

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
