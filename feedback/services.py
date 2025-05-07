"""
Business logic for feedback: submit, view, hide, respond.
"""
from .models import Rating
from accounts.models import User

def submit_rating(**kwargs):
    return Rating.objects.create(**kwargs)

def hide_rating(rating):
    rating.is_hidden = True
    rating.save()
    return rating

def respond_to_rating(rating, response):
    rating.admin_response = response
    rating.save()
    return rating
