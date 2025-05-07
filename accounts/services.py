"""
Business logic for accounts app: registration, authentication, role assignment, etc.
"""
from django.contrib.auth import authenticate, login
from .models import User

# Example: Service to register a user with role

def register_user(username, password, email, role, **profile_data):
    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        role=role,
        **profile_data
    )
    return user

# Example: Service to authenticate and login a user

def login_user(request, username, password):
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
    return user
