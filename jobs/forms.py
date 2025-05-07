from django import forms
from .models import Job, Application

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'schedule', 'location', 'pay']

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume', 'credentials', 'reference_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Explain why you are a good fit for this job...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].widget.attrs.update({'class': 'form-control'})
        self.fields['credentials'].widget.attrs.update({'class': 'form-control'})
        self.fields['reference_letter'].widget.attrs.update({'class': 'form-control'})
        
        # Add help text as labels
        self.fields['resume'].label = 'Resume (PDF or Word document)'
        self.fields['credentials'].label = 'Certifications/Credentials (PDF format)'
        self.fields['reference_letter'].label = 'Reference Letters (Optional)'
