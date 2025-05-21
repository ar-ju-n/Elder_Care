from django import forms
from .models import SystemSetting, NotificationTemplate, ScheduledNotification
from accounts.models import User
from django.contrib.auth.models import Permission

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
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8})
    )
    class Meta:
        model = User
        fields = ['role', 'user_permissions']
