from django.db import models
from accounts.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    image = models.ImageField(upload_to='article_images/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, related_name='articles')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # <-- Added for Last Updated column
    def __str__(self):
        return self.title

class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='videos/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, related_name='videos')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    published_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class HomepageSlide(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='homepage_slides/')
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    ordering = models.PositiveIntegerField(default=0, help_text='Lower comes first')

    class Meta:
        ordering = ['ordering', 'id']

    def __str__(self):
        return self.title

class Link(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

class Guide(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='guides')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    published_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='faqs', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
