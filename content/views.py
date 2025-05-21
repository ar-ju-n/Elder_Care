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

from django.core.paginator import Paginator

def article_list(request):
    # Get all tags for the filter dropdown
    all_tags = Tag.objects.all()

    # Get query params
    search_query = request.GET.get('q', '').strip()
    tag_slug = request.GET.get('tag', '').strip()

    articles = Article.objects.all().order_by('-published_at')

    if search_query:
        articles = articles.filter(
            models.Q(title__icontains=search_query) |
            models.Q(body__icontains=search_query)
        )
    if tag_slug:
        articles = articles.filter(tags__name__iexact=tag_slug)

    articles = articles.distinct()

    # Pagination
    paginator = Paginator(articles, 9)  # 9 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_paginated = page_obj.has_other_pages()

    return render(request, 'content/article_list.html', {
        'articles': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': is_paginated,
        'all_tags': all_tags,
        'search_query': search_query,
        'selected_tag': tag_slug,
    })

def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'content/article_detail.html', {'article': article})

@login_required
@user_passes_test(lambda u: u.is_admin_role())
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            data = form.cleaned_data.copy()
            data.pop('author', None)
            for field, value in data.items():
                setattr(article, field, value)
            article.author = request.user
            article.save()
            form.save_m2m()
            messages.success(request, 'Article updated.')
            return redirect('content:article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'content/article_edit.html', {'form': form, 'article': article})

@login_required
@user_passes_test(lambda u: u.is_admin_role())
def publish_article_view(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            data.pop('author', None)
            article = publish_article(**data, published_by=request.user, author=request.user)
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
