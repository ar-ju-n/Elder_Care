from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Article, Video, Tag
from .services import publish_article, publish_video, add_tag
from accounts.models import User
from django import forms

# Register template tags
from django.template.defaulttags import register

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'body', 'tags']

class VideoForm(forms.ModelForm):
    file = forms.FileField()
    class Meta:
        model = Video
        fields = ['title', 'url', 'file', 'tags']

def article_list(request):
    articles = Article.objects.all().order_by('-published_at')
    return render(request, 'content/article_list.html', {'articles': articles})

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'content/article_detail.html', {'article': article})

@login_required
@user_passes_test(lambda u: u.is_admin_role())
def publish_article_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = publish_article(**form.cleaned_data, published_by=request.user)
            messages.success(request, 'Article published.')
            return redirect('content:article_list')
    else:
        form = ArticleForm()
    return render(request, 'content/publish_article.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_admin_role())
def publish_video_view(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = publish_video(**form.cleaned_data, published_by=request.user)
            messages.success(request, 'Video published.')
            return redirect('content:article_list')
    else:
        form = VideoForm()
    return render(request, 'content/publish_video.html', {'form': form})

def video_list(request):
    videos = Video.objects.all().order_by('-published_at')
    return render(request, 'content/video_list.html', {'videos': videos})

def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return render(request, 'content/video_detail.html', {'video': video})
