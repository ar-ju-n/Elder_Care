from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
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
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Define role choices without admin option
    ROLE_CHOICES = [
        ('elderly', 'Elderly Person'),
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
        fields = ('username', 'email', 'password1', 'password2', 'role')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'bio', 'profile_picture', 'language_preference', 'timezone', 'email_notifications', 'profile_visibility']
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

class CaregiverVerificationForm(forms.ModelForm):
    class Meta:
        from .models import CaregiverVerification
        model = CaregiverVerification
        fields = ['government_id_number', 'address', 'certification_type', 'document']
        widgets = {
            'government_id_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Government ID Number'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'certification_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Certification Type (optional)'}),
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





