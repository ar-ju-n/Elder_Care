from django import template
import re

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of value divided by arg"""
    return int(value) % int(arg)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    return float(value) * float(arg)

def extract_youtube_id(url):
    """Extract YouTube video ID from various URL formats"""
    if not url:
        return None
        
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([\w-]+)',
        r'(?:youtube\.com/v/|youtube\.com/embed/|youtube\.com/watch\?.*v=)([\w-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@register.filter
def youtube_embed(url):
    """
    Converts a YouTube URL to an embeddable format for iframes.
    Supports various YouTube URL formats.
    """
    video_id = extract_youtube_id(url)
    if video_id:
        return f'https://www.youtube.com/embed/{video_id}?rel=0&showinfo=0&autoplay=0'
    return ''

@register.filter
def youtube_embed_id(url):
    """Extract just the YouTube video ID from a URL"""
    return extract_youtube_id(url) or ''

def extract_vimeo_id(url):
    """Extract Vimeo video ID from various URL formats"""
    if not url:
        return None
        
    patterns = [
        r'(?:vimeo\.com/|player\.vimeo\.com/video/)(\d+)',
        r'vimeo\.com/(?:channels/[^/]+/)?(\d+)',
        r'vimeo\.com/groups/[^/]+/videos/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@register.filter
def vimeo_embed(url):
    """
    Converts a Vimeo URL to an embeddable format for iframes.
    Supports various Vimeo URL formats.
    """
    video_id = extract_vimeo_id(url)
    if video_id:
        return f'https://player.vimeo.com/video/{video_id}?title=0&byline=0&portrait=0'
    return ''

@register.filter
def vimeo_embed_id(url):
    """Extract just the Vimeo video ID from a URL"""
    return extract_vimeo_id(url) or ''

@register.filter
def video_thumbnail(url, quality='medium'):
    """
    Generate a thumbnail URL for a video.
    Quality can be: 'default', 'medium', 'high', 'standard', 'maxres'
    """
    youtube_id = extract_youtube_id(url)
    if youtube_id:
        qualities = {
            'default': 'default.jpg',
            'medium': 'mqdefault.jpg',
            'high': 'hqdefault.jpg',
            'standard': 'sddefault.jpg',
            'maxres': 'maxresdefault.jpg'
        }
        quality = qualities.get(quality, 'mqdefault.jpg')
        return f'https://img.youtube.com/vi/{youtube_id}/{quality}'
        
    vimeo_id = extract_vimeo_id(url)
    if vimeo_id:
        # Vimeo requires API call to get thumbnails, so we'll just return a placeholder
        return f'https://vumbnail.com/{vimeo_id}.jpg'
        
    return ''

@register.filter
def video_duration(seconds):
    """Convert duration in seconds to HH:MM:SS format"""
    if not seconds:
        return ''
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return ''
