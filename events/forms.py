"""
Forms for the events app
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Event

class EventForm(forms.ModelForm):
    """Form for creating and updating events"""
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_time', 
            'end_time', 'location'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the input format for datetime fields to match the widget
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Ensure end time is after start time if both are provided
        if start_time and end_time and end_time <= start_time:
            raise ValidationError({
                'end_time': 'End time must be after start time.'
            })
            
        # Ensure start time is in the future
        if start_time and start_time < timezone.now():
            if not self.instance.pk:  # Only for new events
                raise ValidationError({
                    'start_time': 'Start time must be in the future.'
                })
        
        return cleaned_data
