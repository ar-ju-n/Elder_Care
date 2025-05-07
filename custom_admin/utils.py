from django.apps import apps
from django.db.models import Q

def get_app_models_data():
    """
    Get information about all apps and their models in the project.
    
    Returns:
        A list of dictionaries containing app and model information
    """
    app_list = []
    for app_config in apps.get_app_configs():
        if app_config.name.startswith('django.') or app_config.name == 'custom_admin':
            continue
            
        app_dict = {
            'name': app_config.verbose_name,
            'label': app_config.label,
            'models': []
        }
        
        for model in app_config.get_models():
            model_dict = {
                'name': model.__name__,
                'verbose_name': model._meta.verbose_name,
                'verbose_name_plural': model._meta.verbose_name_plural,
                'count': model.objects.count()
            }
            app_dict['models'].append(model_dict)
            
        if app_dict['models']:
            app_list.append(app_dict)
            
    return app_list

def get_model_filters(model):
    """
    Build filter options for a model.
    
    Args:
        model: The model class to build filters for
        
    Returns:
        A dictionary of field names and their filter options
    """
    filters = {}
    for field in model._meta.fields:
        if field.name in ['created_at', 'updated_at', 'id', 'password']:
            continue
            
        if hasattr(field, 'choices') and field.choices:
            filters[field.name] = field.choices
        elif field.get_internal_type() in ['ForeignKey', 'ManyToManyField']:
            related_model = field.related_model
            try:
                options = [(obj.id, str(obj)) for obj in related_model.objects.all()]
                if options:
                    filters[field.name] = options
            except:
                pass
                
    return filters

def filter_queryset(model, queryset, request_data):
    """
    Apply filters to a queryset based on request data.
    
    Args:
        model: The model class
        queryset: The initial queryset
        request_data: Dictionary-like object containing filter parameters
        
    Returns:
        Filtered queryset
    """
    # Apply filters from request
    filter_kwargs = {}
    for key, value in request_data.items():
        if value and key in [f.name for f in model._meta.fields]:
            filter_kwargs[key] = value
    
    if filter_kwargs:
        queryset = queryset.filter(**filter_kwargs)
    
    # Apply search if provided
    search_query = request_data.get('search', '')
    if search_query:
        q_objects = Q()
        for field in model._meta.fields:
            if field.get_internal_type() in ['CharField', 'TextField', 'EmailField']:
                q_objects |= Q(**{f'{field.name}__icontains': search_query})
        queryset = queryset.filter(q_objects)
        
    return queryset
