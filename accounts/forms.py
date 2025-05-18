from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'id': 'id_password1'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'id_password2'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    
    full_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )

    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address'
        })
    )

    rate_per_hour = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rate per hour (NPR) - required for caregivers'
        })
    )


    # Define role choices without admin option
    ROLE_CHOICES = [
        ('caregiver', 'Caregiver'),
        ('family', 'Family Member'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'address', 'profile_picture', 'rate_per_hour', 'password1', 'password2', 'role')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        rate_per_hour = cleaned_data.get('rate_per_hour')
        if role == 'caregiver' and not rate_per_hour:
            self.add_error('rate_per_hour', 'Caregivers must specify their rate per hour.')
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'bio', 'profile_picture', 'language_preference', 'timezone', 'email_notifications', 'profile_visibility']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'language_preference': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_visibility': forms.Select(attrs={'class': 'form-select'})
        }

from .models import CERTIFICATION_CHOICES

class CaregiverVerificationForm(forms.ModelForm):
    certification_type = forms.ChoiceField(
        choices=CERTIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        from .models import CaregiverVerification
        model = CaregiverVerification
        fields = ['government_id_number', 'certification_type', 'document']
        widgets = {
            'government_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Government ID Number'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email_notifications', 'language_preference', 'timezone']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'language_preference': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'})
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    def confirm_login_allowed(self, user):
        if user.is_staff or user.is_superuser:
            raise ValidationError(
                "Admin users cannot log in here.",
                code='invalid_login',
            )

class EmergencyContactForm(forms.ModelForm):
    class Meta:
        from .models import EmergencyContact
        model = EmergencyContact
        fields = ['name', 'relationship', 'phone', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relationship (e.g., Daughter, Doctor)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MedicationReminderForm(forms.ModelForm):
    class Meta:
        from .models import MedicationReminder
        model = MedicationReminder
        fields = ['medication_name', 'dosage', 'notes', 'time_of_day', 'notification_method', 'active']
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medication Name'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dosage (e.g., 1 tablet)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'}),
            'time_of_day': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notification_method': forms.Select(attrs={'class': 'form-select'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }





