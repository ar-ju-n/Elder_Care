from django.db import models
from django.conf import settings
from accounts.models import User

class Rating(models.Model):
    caregiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings', limit_choices_to={'role': 'caregiver'})
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='given_ratings')
    stars = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    review_text = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    admin_response = models.TextField(blank=True)

    def __str__(self):
        return f"{self.caregiver} rated {self.stars} stars"

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.username}"
