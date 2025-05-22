from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class User(AbstractUser):
    # Role choices
    CAREGIVER = 'caregiver'
    FAMILY = 'family'
    ADMIN = 'admin'

    # New fields for family/caregiver registration
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    @property
    def upvotes_received(self):
        # Import here to avoid circular import
        from forum.models import Reply
        return sum(reply.upvotes.count() for reply in self.forum_replies.all())

    @property
    def best_answers(self):
        # Import here to avoid circular import
        from forum.models import Reply
        return self.forum_replies.filter(is_best_answer=True).count()
    
    ROLE_CHOICES = [
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
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=FAMILY)
    def validate_image_size(image):
        max_size = 1024 * 1024  # 1MB
        if image.size > max_size:
            raise ValidationError("Profile picture file size may not exceed 1MB.")

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        validators=[validate_image_size]
    )
    bio = models.TextField(blank=True)
    full_name = models.CharField(max_length=150)  # Required for both family and caregiver
    address = models.CharField(max_length=255)    # Required for both family and caregiver
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone number in international format (e.g., +14155552671)'
    )
    rate_per_hour = models.PositiveIntegerField(null=True, blank=True, help_text="Caregiver's rate per hour in NPR. Only required for caregivers.")  # Already correct: null=True, blank=True
    email_verified = models.BooleanField(default=False, help_text="Whether the user has verified their email address")
    
    # 2FA fields
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Whether 2FA is enabled for this user"
    )
    totp_secret = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        help_text="TOTP secret for 2FA"
    )
    
    # Settings fields
    email_notifications = models.BooleanField(default=True)
    language_preference = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')
    
    # Verification field for caregivers
    is_verified = models.BooleanField(default=False, help_text="Designates whether this caregiver has been verified by an admin.")
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Additional methods to check roles
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

    is_pending_deletion = models.BooleanField(default=False)
    scheduled_deletion_at = models.DateTimeField(null=True, blank=True)

    PUBLIC = 'public'
    PRIVATE = 'private'
    PROFILE_VISIBILITY_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]
    profile_visibility = models.CharField(
        max_length=10,
        choices=PROFILE_VISIBILITY_CHOICES,
        default=PUBLIC,
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone number (e.g., +977 98XXXXXXXX)'
    )

CERTIFICATION_CHOICES = [
    ('nursing', 'Nursing Certificate'),
    ('elderly_care', 'Elderly Care Certification'),
    ('first_aid', 'First Aid/CPR'),
    ('medical_assistant', 'Medical Assistant'),
    ('other', 'Other'),
]

class CaregiverVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='caregiver_verification')
    government_id_number = models.CharField(max_length=100, blank=True)
    certification_type = models.CharField(max_length=100, blank=True, choices=CERTIFICATION_CHOICES)
    document = models.FileField(upload_to='caregiver_documents/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    admin_comment = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Sync user.is_verified with verification status
        if self.approved:
            if not self.user.is_verified:
                self.user.is_verified = True
                from django.utils import timezone
                self.user.verified_at = timezone.now()
                self.user.save()
        else:
            if self.user.is_verified:
                self.user.is_verified = False
                self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Verification for {self.user.username} (Approved: {self.approved})"

# NOTE: After this change, run:
#   python -m pip install --force-reinstall django
#   python manage.py makemigrations
#   python manage.py migrate
# to reset the database and apply the new user model.


class AccountDeletionRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Deletion request for {self.user.username}"

class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.phone}"

class MedicationReminder(models.Model):
    NOTIFY_CHOICES = [
        ('email', 'Email'),
        ('browser', 'Browser'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medication_reminders')
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    time_of_day = models.TimeField()
    notification_method = models.CharField(max_length=10, choices=NOTIFY_CHOICES, default='email')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} at {self.time_of_day} for {self.user.username}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_notifications')
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:40]}..."

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts_sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts_received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}: {self.content[:40]}..."

class ConnectionRequest(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_connection_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_connection_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    message = models.TextField(blank=True, help_text="Optional message to the caregiver")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.get_status_display()})"
    
    def accept(self):
        self.status = self.ACCEPTED
        self.save()
        # Create a connection between users
        self.from_user.connections.add(self.to_user)
        self.to_user.connections.add(self.from_user)
    
    def reject(self):
        self.status = self.REJECTED
        self.save()
