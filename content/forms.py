from django import forms
from .models import Article, Tag

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'})
        }