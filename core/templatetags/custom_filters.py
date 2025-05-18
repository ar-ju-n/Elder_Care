from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def slugify_dir(value):
    """Slugifies the input value for use in URLs/directories."""
    return slugify(value)

@register.filter
def startswith(text, starts):
    """
    Returns True if 'text' starts with 'starts'
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

