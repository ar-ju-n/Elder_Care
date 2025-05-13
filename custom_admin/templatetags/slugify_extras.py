from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def slugify_dir(value):
    """Slugifies a directory name for use in URLs."""
    return slugify(value)
