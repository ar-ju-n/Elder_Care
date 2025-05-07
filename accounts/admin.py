from django.contrib import admin
from .models import User

# We're registering User in custom_admin/admin.py, so we don't need to register it here
# This prevents duplicate registration
