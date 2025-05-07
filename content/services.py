"""
Business logic for content: publishing, tagging, listing.
"""
from .models import Article, Video, Tag
from accounts.models import User

def publish_article(**kwargs):
    return Article.objects.create(**kwargs)

def publish_video(**kwargs):
    return Video.objects.create(**kwargs)

def add_tag(name):
    tag, _ = Tag.objects.get_or_create(name=name)
    return tag
