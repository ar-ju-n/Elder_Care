from django.contrib import admin
from .models import ContactMessage, HomepageSlide, HomepageSlideImage
from django import forms
from django.forms import FileInput
from django.utils.translation import gettext_lazy as _
from adminsortable2.admin import SortableInlineAdminMixin
from django.utils.html import format_html

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('is_read', 'created_at')

class HomepageSlideImageMultiForm(forms.ModelForm):
    image = forms.ImageField(
        label=_('Image'),
        required=False
    )
    class Meta:
        model = HomepageSlideImage
        fields = ('image', 'order')



class HomepageSlideImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = HomepageSlideImage
    extra = 1

from adminsortable2.admin import SortableAdminBase

@admin.register(HomepageSlide)
class HomepageSlideAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [HomepageSlideImageInline]
    list_display = ('title', 'order', 'images_preview')
    ordering = ('order',)

    def images_preview(self, obj):
        return format_html(''.join([
            f'<img src="{img.image.url}" style="max-width:60px; max-height:60px; margin:2px; border-radius:6px;">' for img in obj.images.all()
        ]))
    images_preview.short_description = 'Images Preview'
