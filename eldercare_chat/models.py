from django.db import models
from accounts.models import User

class Assignment(models.Model):
    elderly = models.ForeignKey(User, on_delete=models.CASCADE, related_name='elderly_assignments', limit_choices_to={'role': 'elderly'})
    caregiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='caregiver_assignments', limit_choices_to={'role': 'caregiver'})
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('elderly', 'caregiver')
    
    def __str__(self):
        return f"{self.elderly.username} - {self.caregiver.username}"
    
    def get_other_user(self, user):
        """Get the other user in the assignment"""
        if user == self.elderly:
            return self.caregiver
        elif user == self.caregiver:
            return self.elderly
        return None
    
    def get_last_message(self):
        """Get the last message in this assignment's chat"""
        try:
            chat = self.chat_set.first()
            if chat:
                return chat.message_set.order_by('-timestamp').first()
        except:
            pass
        return None

class Chat(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='chat_set')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat for {self.assignment}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_admin_viewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class CaregiverSkill(models.Model):
    caregiver = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'caregiver'})
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    years_experience = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        unique_together = ('caregiver', 'skill')
    
    def __str__(self):
        return f"{self.caregiver.username} - {self.skill.name}"
