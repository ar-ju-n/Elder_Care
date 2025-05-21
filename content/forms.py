from django import forms
from .models import Article, Tag, Video, HomepageSlide, Guide, FAQ

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
    class Meta:
        model = Video
        fields = ['title', 'url', 'file', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Title'}),
            'url': forms.URLInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Video URL (optional)'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'placeholder': 'Upload Video File'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Tags'})
        }

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