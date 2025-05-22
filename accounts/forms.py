import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import Select
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
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Date of Birth'
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Select'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Gender'
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
        label='City'
    )
    country = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        label='Country'
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

    rate_per_hour = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': "Caregiver's rate per hour in NPR"
        }),
        label='Rate per Hour'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'id': 'id_email'
        }),
        help_text='We\'ll never share your email with anyone else.'
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
    
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (e.g., +977 9XXXXXXXXX)',
        }),
        help_text='Enter a valid international phone number (e.g., +9779812345678, +1 5551234567, +44 2071234567)'
    )
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError('Phone number is required')

        # Accept any international format: +<countrycode> <number> or +<countrycode><number>
        import re
        match = re.match(r'^\+[1-9]\d{0,3} ?\d{6,14}$', phone_number)
        if not match:
            raise forms.ValidationError('Please enter a valid international phone number (e.g., +9779812345678, +1 5551234567, +44 2071234567)')

        # Normalize: remove all spaces before saving
        phone_number = phone_number.replace(' ', '')
        return phone_number



    # Role field - will be set dynamically for this form
    role = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'phone_number', 'address', 'date_of_birth', 'gender', 'city', 'country', 'profile_picture', 'rate_per_hour', 'password1', 'password2', 'role')
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number (e.g., +977 98XXXXXXXX)'
            }),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'})
        }
        help_texts = {
            'phone_number': 'Enter a valid phone number with country code (e.g., +977 98XXXXXXXX)'
        }
        
    def __init__(self, *args, **kwargs):
        role_initial = None
        if 'initial' in kwargs and 'role' in kwargs['initial']:
            role_initial = kwargs['initial']['role']
        elif 'data' in kwargs and 'role' in kwargs['data']:
            role_initial = kwargs['data']['role']
        super().__init__(*args, **kwargs)
        if role_initial:
            self.fields['role'].initial = role_initial
            if role_initial == 'family':
                self.fields['rate_per_hour'].required = False
        self.fields['role'].widget = forms.HiddenInput()
        # Make sure email field is visible and properly configured
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })

    def clean_rate_per_hour(self):
        value = self.cleaned_data.get('rate_per_hour')
        if value in ['', None]:
            return None
        return value

    def clean(self):
        cleaned_data = super().clean()
        # Handle disabled role field
        if 'role' not in cleaned_data and 'role' in self.data:
            cleaned_data['role'] = self.data['role']
        rate_per_hour = cleaned_data.get('rate_per_hour')
        role = cleaned_data.get('role')
        # Only require rate_per_hour for caregivers
        if role == 'caregiver' and not rate_per_hour:
            self.add_error('rate_per_hour', 'Caregivers must specify their rate per hour.')
        # For family, do NOT add error for missing rate_per_hour
        phone_number = cleaned_data.get('phone_number')
        if phone_number:
            cleaned_data['phone_number'] = phone_number
        return cleaned_data

class ProfileForm(forms.ModelForm):
    # Explicitly define phone field to add validation
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (e.g., +977 98XXXXXXXX)'
        }),
        help_text='Enter a valid international phone number (e.g., +9779812345678, +1 5551234567, +44 2071234567)'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'full_name', 'email', 'phone', 'bio', 
            'profile_picture', 'language_preference', 'timezone', 
            'email_notifications', 'profile_visibility'
        ]
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
    
    def clean_phone(self):
        """
        Validate phone number format.
        Valid formats:
        - +9779812345678
        - +1 555 123 4567
        - +44 20 7123 4567
        """
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:  # Phone is optional
            return phone
            
        # Remove all non-digit characters except leading +
        cleaned_phone = ''
        if phone.startswith('+'):
            cleaned_phone = '+'
            phone = phone[1:]
        cleaned_phone += ''.join(c for c in phone if c.isdigit())
        
        # Basic validation: at least 8 digits after country code
        if len(cleaned_phone) < 9 or not cleaned_phone[1:].isdigit():
            raise forms.ValidationError('Enter a valid phone number with country code (e.g., +9779812345678)')
            
        return cleaned_phone

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

class PrivacySettingsForm(forms.ModelForm):
    # Add any additional fields that aren't in the User model as form fields
    show_email = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Show my email address on my profile'
    )
    show_phone = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Show my phone number on my profile'
    )
    show_address = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Show my address on my profile'
    )
    
    class Meta:
        model = User
        fields = [
            'profile_visibility',
            'email_notifications',
            'show_email',
            'show_phone',
            'show_address'
        ]
        widgets = {
            'profile_visibility': forms.Select(attrs={'class': 'form-select'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'profile_visibility': 'Who can see your profile?',
            'email_notifications': 'Receive email notifications',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the custom fields with values from the user's profile or preferences
        if self.instance and hasattr(self.instance, 'userprofile'):
            profile = self.instance.userprofile
            self.fields['show_email'].initial = profile.show_email
            self.fields['show_phone'].initial = profile.show_phone
            self.fields['show_address'].initial = profile.show_address
            
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                profile.show_email = self.cleaned_data['show_email']
                profile.show_phone = self.cleaned_data['show_phone']
                profile.show_address = self.cleaned_data['show_address']
                profile.save()
        return user


class NotificationSettingsForm(forms.ModelForm):
    # Add any additional fields that aren't in the User model as form fields
    push_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Enable push notifications'
    )
    message_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Notify me about new messages'
    )
    job_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Send me job alerts'
    )
    newsletter = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Subscribe to our newsletter'
    )
    
    class Meta:
        model = User
        fields = [
            'email_notifications',
            'push_notifications',
            'message_notifications',
            'job_alerts',
            'newsletter'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'email_notifications': 'Receive email notifications',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the custom fields with values from the user's profile or preferences
        if self.instance and hasattr(self.instance, 'userprofile'):
            profile = self.instance.userprofile
            self.fields['push_notifications'].initial = profile.push_notifications
            self.fields['message_notifications'].initial = profile.message_notifications
            self.fields['job_alerts'].initial = profile.job_alerts
            self.fields['newsletter'].initial = profile.newsletter
            
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                profile.push_notifications = self.cleaned_data['push_notifications']
                profile.message_notifications = self.cleaned_data['message_notifications']
                profile.job_alerts = self.cleaned_data['job_alerts']
                profile.newsletter = self.cleaned_data['newsletter']
                profile.save()
        return user


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





