
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from .models import SystemSetting, NotificationTemplate, ScheduledNotification
from accounts.models import User
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
import pytz
from django.conf import settings

class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ['key', 'value']
        labels = {
            'key': 'Setting Key',
            'value': 'Setting Value',
        }

class NotificationTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate
        fields = ['name', 'subject', 'body']

class ScheduledNotificationForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.SelectMultiple)
    scheduled_for = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    template = forms.ModelChoiceField(queryset=NotificationTemplate.objects.all(), required=False)

    class Meta:
        model = ScheduledNotification
        fields = ['subject', 'body', 'recipients', 'scheduled_for', 'template']

# Enhanced admin notification form for bulk send, schedule, and template
class AdminNotificationForm(forms.Form):
    recipients = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.SelectMultiple, required=True)
    subject = forms.CharField(max_length=200)
    body = forms.CharField(widget=forms.Textarea)
    scheduled_for = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False)
    template = forms.ModelChoiceField(queryset=NotificationTemplate.objects.all(), required=False)

class UserCSVImportForm(forms.Form):
    csv_file = forms.FileField(label="User CSV File", widget=forms.ClearableFileInput(attrs={'accept': '.csv'}))

class EventCSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Event CSV File", widget=forms.ClearableFileInput(attrs={'accept': '.csv'}))

from .models import BrandingSetting

class BrandingSettingForm(forms.ModelForm):
    class Meta:
        model = BrandingSetting
        fields = ['logo', 'theme', 'contact_email', 'contact_phone', 'contact_address']

class UserRolePermissionForm(forms.ModelForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)


class GeneralSettingsForm(forms.Form):
    """Form for general system settings."""
    site_name = forms.CharField(
        max_length=100,
        required=True,
        help_text="The name of the website."
    )
    site_description = forms.CharField(
        widget=forms.Textarea,
        required=False,
        help_text="A brief description of the website."
    )
    time_zone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.all_timezones],
        required=True,
        help_text="The default timezone for the website."
    )
    date_format = forms.ChoiceField(
        choices=[
            ('Y-m-d', 'YYYY-MM-DD'),
            ('m/d/Y', 'MM/DD/YYYY'),
            ('d/m/Y', 'DD/MM/YYYY')
        ],
        required=True,
        help_text="The default date format."
    )
    time_format = forms.ChoiceField(
        choices=[
            ('H:i', '24-hour (14:30)'),
            ('h:i A', '12-hour (2:30 PM)')
        ],
        required=True,
        help_text="The default time format."
    )
    items_per_page = forms.IntegerField(
        min_value=5,
        max_value=100,
        required=True,
        help_text="Number of items to display per page in lists."
    )
    maintenance_mode = forms.BooleanField(
        required=False,
        help_text="When enabled, only administrators can access the site."
    )
    user_registration = forms.BooleanField(
        required=False,
        help_text="Allow new users to register accounts."
    )
    email_verification = forms.BooleanField(
        required=False,
        help_text="Require users to verify their email address."
    )
    enable_analytics = forms.BooleanField(
        required=False,
        help_text="Enable website analytics tracking."
    )
    site_logo = forms.ImageField(
        required=False,
        help_text="The site logo. Recommended size: 250x50px"
    )
    remove_logo = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )


class EmailSettingsForm(forms.Form):
    """Form for email server settings."""
    email_host = forms.CharField(
        max_length=255,
        required=True,
        help_text="The host to use for sending email."
    )
    email_port = forms.IntegerField(
        min_value=1,
        max_value=65535,
        required=True,
        help_text="Port to use for the SMTP server."
    )
    email_host_user = forms.CharField(
        max_length=255,
        required=False,
        help_text="Username to use for the SMTP server."
    )
    email_host_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text="Password to use for the SMTP server. Leave blank to keep current password."
    )
    email_use_tls = forms.BooleanField(
        required=False,
        help_text="Whether to use a TLS (secure) connection when talking to the SMTP server."
    )
    email_use_ssl = forms.BooleanField(
        required=False,
        help_text="Whether to use an implicit TLS (secure) connection when talking to the SMTP server."
    )
    default_from_email = forms.EmailField(
        required=True,
        help_text="Default email address to use for various automated correspondence."
    )
    server_email = forms.EmailField(
        required=False,
        help_text="Email address that error messages come from."
    )
    email_timeout = forms.IntegerField(
        min_value=1,
        max_value=300,
        required=False,
        help_text="Timeout in seconds for blocking operations like the connection attempt."
    )


class SecuritySettingsForm(forms.Form):
    """Form for security-related settings."""
    # Password policy
    password_min_length = forms.IntegerField(
        min_value=4,
        max_value=50,
        initial=8,
        help_text="Minimum length for user passwords (4-50 characters)."
    )
    password_require_uppercase = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Require at least one uppercase letter in passwords."
    )
    password_require_lowercase = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Require at least one lowercase letter in passwords."
    )
    password_require_numbers = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Require at least one number in passwords."
    )
    password_require_symbols = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Require at least one special character in passwords."
    )
    password_expiry_days = forms.IntegerField(
        min_value=0,
        max_value=3650,  # ~10 years
        initial=90,
        help_text="Number of days after which passwords expire (0 to disable)."
    )
    
    # Login security
    login_attempts_limit = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5,
        help_text="Number of failed login attempts before account is locked."
    )
    login_timeout_minutes = forms.IntegerField(
        min_value=1,
        max_value=1440,  # 24 hours
        initial=15,
        help_text="Time in minutes before an inactive user is logged out."
    )
    session_timeout_hours = forms.IntegerField(
        min_value=1,
        max_value=720,  # 30 days
        initial=24,
        help_text="Maximum session duration in hours."
    )
    enable_2fa = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Enable two-factor authentication for all users."
    )
    
    # Security headers
    enable_hsts = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Enable HTTP Strict Transport Security (HSTS)."
    )
    enable_xss_protection = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Enable XSS filter in the browser."
    )
    enable_content_security_policy = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Enable Content Security Policy (CSP) headers."
    )
    enable_referrer_policy = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Enable Referrer-Policy header."
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email_use_tls = cleaned_data.get('email_use_tls')
        email_use_ssl = cleaned_data.get('email_use_ssl')
        
        if email_use_tls and email_use_ssl:
            raise ValidationError("TLS and SSL are mutually exclusive. Please select only one.")
        
        return cleaned_data
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8})
    )
    class Meta:
        model = User
        fields = ['role', 'user_permissions']
