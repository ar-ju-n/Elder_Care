from django import template

register = template.Library()

@register.filter
def startswith(text, starts):
    """
    Returns True if 'text' starts with 'starts'
    """
    if isinstance(text, str):
        return text.startswith(starts)
    return False

