"""
Business logic for eldercare chat: chat creation, messaging, assignment.
"""
from .models import Assignment, Chat, Message
from accounts.models import User

def assign_caregiver_to_elderly(elderly, caregiver):
    return Assignment.objects.create(elderly=elderly, caregiver=caregiver)

def create_chat(assignment):
    return Chat.objects.create(assignment=assignment)

def send_message(chat, sender, content):
    return Message.objects.create(chat=chat, sender=sender, content=content)
