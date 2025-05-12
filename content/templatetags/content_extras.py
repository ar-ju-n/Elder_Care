from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return int(value) % int(arg)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    return float(value) * float(arg)

@register.filter
def youtube_embed(url):
    """
    Converts a YouTube URL to an embeddable format for iframes.
    Supports both youtube.com and youtu.be links.
    """
    import re
    if not url:
        return ''
    # Match youtube.com/watch?v= or youtu.be/ links
    patterns = [
        r'youtube\.com/watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)'
    ]
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    if video_id:
        return f'https://www.youtube.com/embed/{video_id}'
    return url
