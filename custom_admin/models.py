from django.db import models
from django.utils.html import mark_safe


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.email})"


class HomepageSlide(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    photo = models.ImageField(upload_to='homepage_slides/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Homepage Slide'
        verbose_name_plural = 'Homepage Slides'

    def __str__(self):
        return self.title


class HomepageSlideImage(models.Model):
    slide = models.ForeignKey(HomepageSlide, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='homepage_slides/images/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Homepage Slide Image'
        verbose_name_plural = 'Homepage Slide Images'

    def __str__(self):
        return f"Image for {self.slide.title} (#{self.order})"
