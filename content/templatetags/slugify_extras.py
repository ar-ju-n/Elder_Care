from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def slugify_extras(value):
    """
    Slugify the given string (lowercase, hyphens, safe for URLs).
    Usage: {{ value|slugify_extras }}
    """
    return slugify(value)
