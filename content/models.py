from django.db import models
from accounts.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='articles')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    published_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    tags = models.ManyToManyField(Tag, related_name='videos')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    published_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title
