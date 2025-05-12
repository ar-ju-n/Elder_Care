from django.contrib import admin
from .models import ContactMessage, ThemeSetting, DynamicPage, ContentBlock
from django import forms
from django.utils.safestring import mark_safe

from django.utils.html import format_html

class ContentBlockAdminForm(forms.ModelForm):
    background = forms.CharField(required=False, label="Background Color (hex)", widget=forms.TextInput(attrs={'type': 'color'}))
    text_color = forms.CharField(required=False, label="Text Color (hex)", widget=forms.TextInput(attrs={'type': 'color'}))
    border_color = forms.CharField(required=False, label="Border Color (hex)", widget=forms.TextInput(attrs={'type': 'color'}))
    padding = forms.CharField(required=False, label="Padding (px)", help_text="e.g. 24 for 24px")
    animation = forms.ChoiceField(
        required=False,
        label="Animation",
        choices=[
            ("", "None"),
            ("fade-in", "Fade In"),
            ("slide-up", "Slide Up"),
            ("bounce", "Bounce"),
            ("zoom-in", "Zoom In"),
            ("flip", "Flip"),
            ("pulse", "Pulse"),
            ("shake", "Shake"),
        ],
        help_text="Choose an animation for this block."
    )
    font_size = forms.CharField(required=False, label="Font Size (px)", help_text="e.g. 18 for 18px")
    border_radius = forms.CharField(required=False, label="Border Radius (px)", help_text="e.g. 8 for 8px")
    font_family = forms.CharField(required=False, label="Font Family", help_text="e.g. Arial, 'Open Sans', etc.")
    box_shadow = forms.CharField(required=False, label="Box Shadow", help_text="e.g. 0px 4px 12px #00000033")
    text_align = forms.ChoiceField(required=False, label="Text Align", choices=[('', 'Default'), ('left', 'Left'), ('center', 'Center'), ('right', 'Right'), ('justify', 'Justify')])
    margin = forms.CharField(required=False, label="Margin (px)", help_text="e.g. 24 for 24px")
    shadow_color = forms.CharField(required=False, label="Shadow Color (hex)", widget=forms.TextInput(attrs={'type': 'color'}), help_text="Color for box/text shadow")
    show_on_desktop = forms.BooleanField(required=False, label="Show on Desktop", initial=True)
    show_on_mobile = forms.BooleanField(required=False, label="Show on Mobile", initial=True)
    opacity = forms.FloatField(required=False, label="Opacity (0-1)", min_value=0, max_value=1, help_text="0 = transparent, 1 = opaque")
    letter_spacing = forms.CharField(required=False, label="Letter Spacing (px)", help_text="e.g. 2 for 2px")
    line_height = forms.CharField(required=False, label="Line Height", help_text="e.g. 1.5 or 24px")
    max_width = forms.CharField(required=False, label="Max Width (px)", help_text="e.g. 600 for 600px")
    border_style = forms.ChoiceField(required=False, label="Border Style", choices=[('', 'Default'), ('solid', 'Solid'), ('dashed', 'Dashed'), ('dotted', 'Dotted'), ('double', 'Double')])
    border_width = forms.CharField(required=False, label="Border Width (px)", help_text="e.g. 2 for 2px")
    background_gradient = forms.CharField(required=False, label="Background Gradient (CSS)", help_text="e.g. linear-gradient(#e66465, #9198e5)")
    custom_class = forms.CharField(required=False, label="Custom CSS Class(es)", help_text="Space-separated extra CSS classes")

    class Meta:
        model = ContentBlock
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'class': 'richtext-editor', 'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = self.instance.style if hasattr(self.instance, 'style') and isinstance(self.instance.style, dict) else {}
        # Prepopulate style fields
        self.fields['background'].initial = style.get('background', '')
        self.fields['text_color'].initial = style.get('text_color', '')
        self.fields['border_color'].initial = style.get('border_color', '')
        self.fields['padding'].initial = style.get('padding', '')
        self.fields['animation'].initial = style.get('animation', '')
        self.fields['font_size'].initial = style.get('font_size', '')
        self.fields['border_radius'].initial = style.get('border_radius', '')
        self.fields['font_family'].initial = style.get('font_family', '')
        self.fields['box_shadow'].initial = style.get('box_shadow', '')
        self.fields['text_align'].initial = style.get('text_align', '')
        self.fields['margin'].initial = style.get('margin', '')
        self.fields['shadow_color'].initial = style.get('shadow_color', '')
        self.fields['show_on_desktop'].initial = style.get('show_on_desktop', True)
        self.fields['show_on_mobile'].initial = style.get('show_on_mobile', True)
        self.fields['opacity'].initial = style.get('opacity', '')
        self.fields['letter_spacing'].initial = style.get('letter_spacing', '')
        self.fields['line_height'].initial = style.get('line_height', '')
        self.fields['max_width'].initial = style.get('max_width', '')
        self.fields['border_style'].initial = style.get('border_style', '')
        self.fields['border_width'].initial = style.get('border_width', '')
        self.fields['background_gradient'].initial = style.get('background_gradient', '')
        self.fields['custom_class'].initial = style.get('custom_class', '')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = self.instance.style if hasattr(self.instance, 'style') and isinstance(self.instance.style, dict) else {}
        self.fields['background'].initial = style.get('background', '')
        self.fields['text_color'].initial = style.get('text_color', '')
        self.fields['border_color'].initial = style.get('border_color', '')
        self.fields['padding'].initial = style.get('padding', '')
        self.fields['animation'].initial = style.get('animation', '')
        self.fields['font_size'].initial = style.get('font_size', '')
        self.fields['border_radius'].initial = style.get('border_radius', '')
        self.fields['font_family'].initial = style.get('font_family', '')
        self.fields['box_shadow'].initial = style.get('box_shadow', '')
        self.fields['text_align'].initial = style.get('text_align', '')
        self.fields['margin'].initial = style.get('margin', '')
        self.fields['shadow_color'].initial = style.get('shadow_color', '')
        self.fields['show_on_desktop'].initial = style.get('show_on_desktop', True)
        self.fields['show_on_mobile'].initial = style.get('show_on_mobile', True)

    def clean(self):
        cleaned_data = super().clean()
        style = self.instance.style if hasattr(self.instance, 'style') and isinstance(self.instance.style, dict) else {}
        # Style controls
        style['background'] = cleaned_data.get('background', '')
        style['text_color'] = cleaned_data.get('text_color', '')
        style['border_color'] = cleaned_data.get('border_color', '')
        style['padding'] = cleaned_data.get('padding', '')
        style['animation'] = cleaned_data.get('animation', '')
        style['font_size'] = cleaned_data.get('font_size', '')
        style['border_radius'] = cleaned_data.get('border_radius', '')
        style['font_family'] = cleaned_data.get('font_family', '')
        style['box_shadow'] = cleaned_data.get('box_shadow', '')
        style['text_align'] = cleaned_data.get('text_align', '')
        style['margin'] = cleaned_data.get('margin', '')
        style['shadow_color'] = cleaned_data.get('shadow_color', '')
        style['show_on_desktop'] = cleaned_data.get('show_on_desktop', True)
        style['show_on_mobile'] = cleaned_data.get('show_on_mobile', True)
        style['opacity'] = cleaned_data.get('opacity', '')
        style['letter_spacing'] = cleaned_data.get('letter_spacing', '')
        style['line_height'] = cleaned_data.get('line_height', '')
        style['max_width'] = cleaned_data.get('max_width', '')
        style['border_style'] = cleaned_data.get('border_style', '')
        style['border_width'] = cleaned_data.get('border_width', '')
        style['background_gradient'] = cleaned_data.get('background_gradient', '')
        style['custom_class'] = cleaned_data.get('custom_class', '')
        # Remove empty keys (but keep booleans)
        style = {k: v for k, v in style.items() if (v or isinstance(v, bool))}
        cleaned_data['style'] = style
        return cleaned_data

    class Media:
        js = ('js/contentblock_live_preview.js',)

@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    form = ContentBlockAdminForm
    list_display = ('page', 'order', 'block_type', 'block_title', 'is_visible')
    list_filter = ('block_type', 'is_visible', 'page', 'collapsible')
    search_fields = ('content', 'block_title', 'button_text', 'button_url')
    ordering = ('page', 'order')
    fieldsets = (
        (None, {
            'fields': ('page', 'order', 'block_type', 'block_title', 'icon', 'collapsible', 'html_tag', 'condition', 'is_visible')
        }),
        ('Content', {
            'fields': ('content', 'button_text', 'button_url', 'button_style'),
        }),
        ('Style', {
            'fields': (
                'background', 'background_gradient', 'text_color', 'font_family', 'font_size', 'line_height', 'letter_spacing', 'max_width',
                'border_color', 'border_style', 'border_width', 'border_radius', 'box_shadow', 'shadow_color',
                'padding', 'margin', 'opacity', 'animation', 'custom_class', 'text_align',
                'show_on_desktop', 'show_on_mobile',
            ),
        }),
    )

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="max-height:32px;max-width:32px;" />', obj.icon.url)
        return ""
    icon_preview.short_description = "Icon Preview"

@admin.register(DynamicPage)
class DynamicPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active')
    search_fields = ('title', 'slug')
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ('is_active',)

@admin.register(ThemeSetting)
class ThemeSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_color', 'secondary_color', 'background_color', 'font_family')
    search_fields = ('name',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('is_read', 'created_at')

# Register your models here.
