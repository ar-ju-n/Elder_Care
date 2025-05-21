from django import forms
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
