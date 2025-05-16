from django import forms
from django.apps import apps

def get_model_form(app_label, model_name, exclude_fields=None):
    """
    Dynamically create a ModelForm for any model in the project.
    
    Args:
        app_label: The app label for the model
        model_name: The name of the model
        exclude_fields: List of fields to exclude from the form
        
    Returns:
        A ModelForm class for the specified model
    """
    if exclude_fields is None:
        exclude_fields = []
        
    # Get the model class from the app_label and model_name
    model_class = apps.get_model(app_label, model_name)
    
    # Create a ModelForm class for the model
    class DynamicModelForm(forms.ModelForm):
        class Meta:
            model = model_class  # Use model_class instead of model
            exclude = exclude_fields
            
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Add Bootstrap classes to all form fields
            for field_name, field in self.fields.items():
                if field.widget.__class__.__name__ not in ['CheckboxInput', 'RadioSelect']:
                    field.widget.attrs['class'] = 'form-control'
                else:
                    field.widget.attrs['class'] = 'form-check-input'
                # Render DateTimeField as <input type="datetime-local">
                if hasattr(field, 'widget') and isinstance(field.widget, forms.DateTimeInput):
                    field.widget.input_type = 'datetime-local'
                    # Format initial value for browser compatibility
                    if self.initial.get(field_name):
                        dt = self.initial[field_name]
                        if hasattr(dt, 'strftime'):
                            self.initial[field_name] = dt.strftime('%Y-%m-%dT%H:%M')
                    
    return DynamicModelForm
