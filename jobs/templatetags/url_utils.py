from django import template
from urllib.parse import urlencode, parse_qs, urlparse, urlunparse

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Replace or add query parameters in the current URL.
    Usage: {% url_replace param1='value1' param2='value2' %}
    """
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return query.urlencode()

@register.filter
def remove_param(url, param_name):
    """
    Remove a parameter from URL query string.
    Usage: {{ request.get_full_path|remove_param:'param_name' }}
    """
    url_parts = list(urlparse(url))
    query = parse_qs(url_parts[4])
    
    if param_name in query:
        del query[param_name]
    
    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)

@register.filter
def add_param(url, param):
    """
    Add or update a parameter in URL query string.
    Usage: {{ request.get_full_path|add_param:'param_name=value' }}
    """
    if '=' not in param:
        return url
        
    param_name, param_value = param.split('=', 1)
    url_parts = list(urlparse(url))
    query = parse_qs(url_parts[4])
    
    # Update or add the parameter
    query[param_name] = [param_value]
    
    url_parts[4] = urlencode(query, doseq=True)
    return urlunparse(url_parts)
