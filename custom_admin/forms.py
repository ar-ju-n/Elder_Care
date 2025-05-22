from django import forms
from django.contrib.auth.models import Group, Permission
from accounts.models import User, Notification
from events.models import Event
from content.models import Article, Link
from .models import Integration

class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'role', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
        }

class AdminEventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_time', 'end_time', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Event Description'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
        }

class AdminNotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['recipient', 'message', 'url']

class AdminArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body', 'image', 'tags', 'published_by']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Article Title'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Article Content'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'published_by': forms.Select(attrs={'class': 'form-control'}),
        }

class AdminLinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['title', 'description', 'url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Link Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 2, 'placeholder': 'Short Description'}),
            'url': forms.URLInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'https://example.com'}),
        }

class UserRoleForm(forms.ModelForm):
    """
    Form for managing user roles and permissions in the admin panel.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Groups'
    )
    
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
        required=False,
        label='Additional Permissions',
        help_text='Specific permissions for this user.'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['user_permissions'].queryset = Permission.objects.select_related('content_type')


class AdminIntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ['name', 'service_type', 'status', 'config']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Integration Name'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Status'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Configuration (JSON)'}),
        }
