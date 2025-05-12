from django.db import models
from django.utils.html import mark_safe

# Global theme settings
class ThemeSetting(models.Model):
    name = models.CharField(max_length=50, unique=True, default="default")
    primary_color = models.CharField(max_length=7, default="#007bff")
    secondary_color = models.CharField(max_length=7, default="#6c757d")
    background_color = models.CharField(max_length=7, default="#ffffff")
    font_family = models.CharField(max_length=100, default="Inter, sans-serif")
    custom_css = models.TextField(blank=True, help_text="Custom CSS to inject site-wide.")

    def __str__(self):
        return self.name

# Dynamic pages (e.g. /about, /contact, /)
class DynamicPage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    meta_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

# Content blocks for each page
class ContentBlock(models.Model):
    BLOCK_TYPE_CHOICES = [
        ("text", "Text"),
        ("image", "Image"),
        ("cta", "Call To Action"),
        ("custom_html", "Custom HTML"),
    ]
    page = models.ForeignKey(DynamicPage, on_delete=models.CASCADE, related_name="blocks")
    order = models.PositiveIntegerField(default=0)
    block_type = models.CharField(max_length=50, choices=BLOCK_TYPE_CHOICES, default="text")
    block_title = models.CharField(max_length=200, blank=True, help_text="Optional title/heading for this block")
    icon = models.ImageField(upload_to='block_icons/', blank=True, null=True, help_text="Optional icon for this block")
    button_text = models.CharField(max_length=100, blank=True, help_text="Text for button/link")
    button_url = models.URLField(blank=True, help_text="URL for button/link")
    button_style = models.CharField(max_length=100, blank=True, help_text="Button style class(es)")
    collapsible = models.BooleanField(default=False, help_text="Make this block collapsible/expandable")
    html_tag = models.CharField(max_length=20, blank=True, default='div', help_text="HTML tag for this block (div, section, article, etc.)")
    condition = models.CharField(max_length=100, blank=True, help_text="Condition for display (e.g., user_logged_in)")
    content = models.TextField(help_text="Content (rich text supported)")
    style = models.JSONField(default=dict, blank=True, help_text="Per-block CSS or options as JSON")
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.page.title} - Block {self.order} ({self.block_type})"

    def rendered_content(self):
        return mark_safe(self.content)

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.email})"
