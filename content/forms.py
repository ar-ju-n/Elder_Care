import os
from django import forms
from .models import Article, Tag, Video, HomepageSlide, Guide, FAQ, Link

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body', 'tags', 'author']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Title'}),
            'body': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 10, 'placeholder': 'Body'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Tags'})
        }

class VideoForm(forms.ModelForm):
    # Add a video type selector
    VIDEO_TYPE_CHOICES = [
        ('url', 'External URL'),
        ('file', 'Upload Video'),
    ]
    video_type = forms.ChoiceField(
        choices=VIDEO_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        initial='url',
        required=True
    )
    
    # Make URL and file fields not required at the form level
    # We'll handle validation in clean()
    url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.youtube.com/watch?v=... or https://vimeo.com/...',
            'data-video-type': 'url'
        })
    )
    
    file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'video/*',
            'data-video-type': 'file'
        }),
        help_text='Maximum file size: 100MB. Supported formats: MP4, WebM, Ogg.'
    )
    
    # Add a clear file checkbox for existing files
    clear_file = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_type', 'url', 'file', 'thumbnail', 'tags', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter video description',
                'required': 'required'
            }),
            'video_type': forms.RadioSelect(attrs={
                'class': 'video-type-radio',
                'required': 'required'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/video',
                'data-video-type': 'url'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*',
                'data-video-type': 'file'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control tag-input',
                'placeholder': 'Add tags',
                'data-role': 'tagsinput'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for the video type radio buttons
        if self.instance and self.instance.pk:
            if self.instance.file:
                self.fields['video_type'].initial = 'file'
            elif self.instance.url:
                self.fields['video_type'].initial = 'url'
            
            # Convert tags to comma-separated string for the input
            if hasattr(self.instance, 'tags') and 'tags' in self.fields:
                self.initial['tags'] = ', '.join(tag.name for tag in self.instance.tags.all())
        
        # Make sure the clear_file field is properly initialized
        if 'clear_file' in self.fields:
            self.fields['clear_file'].widget = forms.HiddenInput()
            self.fields['clear_file'].required = False
            
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if field_name != 'tags':  # Skip tags as it's handled specially
                if 'class' in field.widget.attrs:
                    if 'form-control' not in field.widget.attrs['class']:
                        field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        return tags
    
    def clean(self):
        cleaned_data = super().clean()
        video_type = cleaned_data.get('video_type')
        
        # Validate either URL or file is provided based on video_type
        if video_type == 'url' and not cleaned_data.get('url'):
            self.add_error('url', 'URL is required for external videos')
        elif video_type == 'file' and not cleaned_data.get('file') and not self.instance.file:
            self.add_error('file', 'Please upload a video file')
            
        return cleaned_data
    
    class Meta:
        model = Video
        fields = ['title', 'url', 'file', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=... or https://vimeo.com/...'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select or add tags',
                'style': 'width: 100%',
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        
        # Set initial video type based on instance data
        if instance and instance.pk:
            if instance.file:
                self.fields['video_type'].initial = 'file'
            elif instance.url:
                self.fields['video_type'].initial = 'url'
        
        # Set up the tags field with create option
        self.fields['tags'].queryset = Tag.objects.all()
        self.fields['tags'].required = False
        
        # Set required fields
        self.fields['title'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        video_type = cleaned_data.get('video_type')
        url = cleaned_data.get('url')
        file = cleaned_data.get('file')
        clear_file = cleaned_data.get('clear_file')
        
        # If we're clearing an existing file, no need for further validation
        if clear_file and self.instance and self.instance.file:
            return cleaned_data
        
        # Validate based on video type
        if video_type == 'url':
            if not url:
                self.add_error('url', 'Please enter a valid video URL')
            # Clear file data if URL is provided
            if 'file' in self.files:
                del self.files['file']
            cleaned_data['file'] = None
        else:  # file upload
            if not file and not (self.instance and self.instance.file):
                self.add_error('file', 'Please select a video file to upload')
            # Clear URL if file is uploaded
            cleaned_data['url'] = ''
        
        # Ensure at least one of url or file is provided
        if not url and not file and not (self.instance and self.instance.file):
            raise forms.ValidationError('Please provide either a video URL or upload a video file')
        
        return cleaned_data
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (100MB max)
            max_size = 100 * 1024 * 1024  # 100MB
            if file.size > max_size:
                raise forms.ValidationError(f'File too large. Maximum size is {max_size/1024/1024}MB')
            
            # Validate file type
            valid_extensions = ['.mp4', '.webm', '.ogg', '.mov']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.validationError('Unsupported file format. Please upload a video file (MP4, WebM, OGG, MOV).')
            
            # Validate content type
            content_type = file.content_type.split('/')[0]
            if content_type != 'video':
                raise forms.ValidationError('File is not a video.')
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle file clearing
        if self.cleaned_data.get('clear_file'):
            instance.file.delete(save=False)
        
        # Set published_by if new video
        if not instance.pk and hasattr(self, 'request_user'):
            instance.published_by = self.request_user
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance

class HomepageSlideForm(forms.ModelForm):
    class Meta:
        model = HomepageSlide
        fields = ['title', 'image', 'description', 'link', 'ordering']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Title'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'placeholder': 'Upload Slide Image'}),
            'description': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Description', 'rows': 2}),
            'link': forms.URLInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Optional Link'}),
            'ordering': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Order'})
        }

class GuideForm(forms.ModelForm):
    class Meta:
        model = Guide
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 10, 'placeholder': 'Guide Content'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Tags'})
        }

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'tags']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Question'}),
            'answer': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'rows': 5, 'placeholder': 'Answer'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Tags'})
        }


class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['title', 'description', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-white',
                'placeholder': 'Link Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white',
                'rows': 3,
                'placeholder': 'Description (optional)'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control bg-dark text-white',
                'placeholder': 'https://example.com'
            })
        }
        help_texts = {
            'url': 'Enter a valid URL including http:// or https://'
        }