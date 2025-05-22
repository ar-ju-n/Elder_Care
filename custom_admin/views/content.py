"""
Content Management Views for Custom Admin
"""
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator

from content.models import Article, Video, HomepageSlide, Link, Tag, Guide, FAQ
from content.forms import ArticleForm, VideoForm, HomepageSlideForm, GuideForm, FAQForm, LinkForm
from core.models import AuditLog

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

# Article Views
@login_required
@user_passes_test(is_admin)
def content_management(request):
    """
    Content management dashboard showing overview of all content types.
    """
    # Get content counts for the dashboard
    content_counts = {
        'articles': Article.objects.count(),
        'videos': Video.objects.count(),
        'links': Link.objects.count(),
        'guides': Guide.objects.count(),
        'faqs': FAQ.objects.count(),
        'tags': Tag.objects.count(),
    }
    
    # Get recent activities from audit log
    recent_activities = AuditLog.objects.filter(
        action__in=['add_article', 'update_article', 'delete_article',
                   'add_video', 'update_video', 'delete_video',
                   'add_link', 'update_link', 'delete_link',
                   'add_guide', 'update_guide', 'delete_guide',
                   'add_faq', 'update_faq', 'delete_faq']
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': 'Content Management',
        'active_tab': 'content',
        'content_counts': content_counts,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'custom_admin/content_management.html', context)


def article_list(request):
    """List all articles"""
    articles = Article.objects.all().order_by('-published_at')
    return render(request, 'custom_admin/article_list.html', {'articles': articles})

@login_required
@user_passes_test(is_admin)
def article_add(request):
    """Add a new article"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()
            messages.success(request, 'Article added successfully.')
            return redirect('custom_admin:content:article_list')
    else:
        form = ArticleForm()
    return render(request, 'custom_admin/article_add.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def article_edit(request, article_id):
    """Edit an existing article"""
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article updated successfully.')
            return redirect('custom_admin:content:article_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'custom_admin/article_edit.html', {'form': form, 'action': 'Edit', 'article': article})

@login_required
@user_passes_test(is_admin)
def article_delete(request, article_id):
    """Delete an article"""
    article = get_object_or_404(Article, id=article_id)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted successfully.')
    return redirect('custom_admin:content:article_list')

# Video Views

@login_required
@user_passes_test(is_admin)
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article.delete()
    messages.success(request, 'Article deleted successfully.')
    return redirect('custom_admin:content:article_list')

@login_required
@user_passes_test(is_admin)
def video_list(request):
    """List all videos with pagination"""
    videos = Video.objects.all().order_by('-published_at')
    paginator = Paginator(videos, 10)  # Show 10 videos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_videos = videos.count()
    search_query = request.GET.get('search', '')
    return render(request, 'custom_admin/video_list.html', {
        'page_obj': page_obj,
        'total_videos': total_videos,
        'search_query': search_query,
    })

@login_required
@user_passes_test(is_admin)
def video_add(request):
    """Add a new video"""
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.added_by = request.user
            video.save()
            
            # Handle tags
            tags = form.cleaned_data.get('tags', [])
            if tags:
                video.tags.set(tags)
            
            messages.success(request, 'Video added successfully.')
            return redirect('custom_admin:content:video_list')
    else:
        form = VideoForm()
    return render(request, 'custom_admin/video_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def video_edit(request, video_id):
    """Edit an existing video"""
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            video = form.save(commit=False)
            video.save()
            
            # Handle tags
            tags = form.cleaned_data.get('tags', [])
            if tags is not None:  # Only update if tags were provided
                from django.template.defaultfilters import slugify
                from content.models import Tag
                
                # Clear existing tags
                video.tags.clear()
                
                # Add new tags
                for tag_name in tags:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': slugify(tag_name)}
                    )
                    video.tags.add(tag)
            
            messages.success(request, 'Video updated successfully.')
            return redirect('custom_admin:content:video_list')
    else:
        # Initialize form with current tags as comma-separated string
        initial = {}
        if video.tags.exists():
            initial['tags'] = ', '.join(tag.name for tag in video.tags.all())
        form = VideoForm(instance=video, initial=initial)
    
    return render(request, 'custom_admin/video_form.html', {
        'form': form, 
        'action': 'Edit',
        'video': video
    })

@login_required
@user_passes_test(is_admin)
def video_delete(request, video_id):
    """Delete a video"""
    video = get_object_or_404(Video, id=video_id)
    if request.method == 'POST':
        video.delete()
        messages.success(request, 'Video deleted successfully.')
    return redirect('custom_admin:content:video_list')

# Link Views
@login_required
@user_passes_test(is_admin)
def link_list(request):
    """List all links"""
    links = Link.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/link_list.html', {'links': links})

@login_required
@user_passes_test(is_admin)
def link_add(request):
    """Add a new link"""
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.created_by = request.user
            link.save()
            messages.success(request, 'Link added successfully.')
            return redirect('custom_admin:content:link_list')
    else:
        form = LinkForm()
    return render(request, 'custom_admin/link_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def link_edit(request, link_id):
    """Edit an existing link"""
    link = get_object_or_404(Link, id=link_id)
    if request.method == 'POST':
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, 'Link updated successfully.')
            return redirect('custom_admin:content:link_list')
    else:
        form = LinkForm(instance=link)
    return render(request, 'custom_admin/link_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def link_delete(request, link_id):
    """Delete a link"""
    link = get_object_or_404(Link, id=link_id)
    if request.method == 'POST':
        link.delete()
        messages.success(request, 'Link deleted successfully.')
        return redirect('custom_admin:content:link_list')
    return render(request, 'custom_admin/confirm_delete_link.html', {'link': link})

# Homepage Slide Views
from django.views.decorators.http import require_http_methods

@login_required
@user_passes_test(is_admin)
def slide_list(request):
    slides = HomepageSlide.objects.all().order_by('ordering')
    return render(request, 'custom_admin/slide_list.html', {'slides': slides})

@login_required
@user_passes_test(is_admin)
def slide_add(request):
    if request.method == 'POST':
        form = HomepageSlideForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Homepage slide added successfully.')
            return redirect('custom_admin:slide_list')
    else:
        form = HomepageSlideForm()
    return render(request, 'custom_admin/slide_add.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def slide_edit(request, slide_id):
    slide = get_object_or_404(HomepageSlide, id=slide_id)
    if request.method == 'POST':
        form = HomepageSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Homepage slide updated successfully.')
            return redirect('custom_admin:slide_list')
    else:
        form = HomepageSlideForm(instance=slide)
    return render(request, 'custom_admin/slide_edit.html', {'form': form, 'slide': slide})

@login_required
@user_passes_test(is_admin)
def slide_delete(request, slide_id):
    slide = get_object_or_404(HomepageSlide, id=slide_id)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Homepage slide deleted successfully.')
        return redirect('custom_admin:slide_list')
    return render(request, 'custom_admin/confirm_delete_slide.html', {'object': slide, 'type': 'Homepage Slide'})

# Guide Views
@login_required
@user_passes_test(is_admin)
def guide_list(request):
    """List all guides"""
    guides = Guide.objects.all().order_by('-published_at')
    return render(request, 'custom_admin/guide_list.html', {'guides': guides})

@login_required
@user_passes_test(is_admin)
def guide_add(request):
    """Add a new guide"""
    if request.method == 'POST':
        form = GuideForm(request.POST)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.published_by = request.user
            guide.save()
            form.save_m2m()
            return redirect('custom_admin:content:guide_list')
    else:
        form = GuideForm()
    return render(request, 'custom_admin/guide_form.html', {'form': form, 'action': 'Add'})



@login_required
@user_passes_test(is_admin)
def guide_edit(request, guide_id):
    """Edit an existing guide"""
    guide = get_object_or_404(Guide, id=guide_id)
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guide updated successfully.')
            return redirect('custom_admin:content:guide_list')
    else:
        form = GuideForm(instance=guide)
    return render(request, 'custom_admin/guide_edit.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def guide_delete(request, guide_id):
    """Delete a guide"""
    guide = get_object_or_404(Guide, id=guide_id)
    if request.method == 'POST':
        guide.delete()
        messages.success(request, 'Guide deleted successfully.')
        return redirect('custom_admin:content:guide_list')
    return render(request, 'custom_admin/confirm_delete.html', 
                 {'object': guide, 'cancel_url': reverse('custom_admin:content:guide_list')})

# FAQ Views
@login_required
@user_passes_test(is_admin)
def faq_list(request):
    """List all FAQs"""
    faqs = FAQ.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/faq_list.html', {'faqs': faqs})

@login_required
@user_passes_test(is_admin)
def faq_add(request):
    """Add a new FAQ"""
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ added successfully.')
            return redirect('custom_admin:content:faq_list')
    else:
        form = FAQForm()
    return render(request, 'custom_admin/faq_add.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def faq_edit(request, faq_id):
    """Edit an existing FAQ"""
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            messages.success(request, 'FAQ updated successfully.')
            return redirect('custom_admin:content:faq_list')
    else:
        form = FAQForm(instance=faq)
    return render(request, 'custom_admin/faq_edit.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def faq_delete(request, faq_id):
    """Delete an FAQ"""
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        faq.delete()
        messages.success(request, 'FAQ deleted successfully.')
        return redirect('custom_admin:content:faq_list')
    return render(request, 'custom_admin/confirm_delete.html', 
                 {'object': faq, 'cancel_url': reverse('custom_admin:content:faq_list')})

# Tag Views
@login_required
@user_passes_test(is_admin)
def tag_list(request):
    """List all tags"""
    tags = Tag.objects.all().order_by('name')
    return render(request, 'custom_admin/tag_list.html', {'tags': tags})

@login_required
@user_passes_test(is_admin)
def tag_add(request):
    """Add a new tag"""
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Tag.objects.get_or_create(name=name)
            messages.success(request, 'Tag added successfully.')
            return redirect('custom_admin:content:tag_list')
    return render(request, 'custom_admin/tag_add.html', {'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def tag_edit(request, tag_id):
    """Edit an existing tag"""
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name and name != tag.name:
            tag.name = name
            tag.save()
            messages.success(request, 'Tag updated successfully.')
            return redirect('custom_admin:content:tag_list')
    return render(request, 'custom_admin/tag_edit.html', {'tag': tag, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def tag_delete(request, tag_id):
    """Delete a tag"""
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('custom_admin:content:tag_list')
    return render(request, 'custom_admin/confirm_delete.html', 
                 {'object': tag, 'cancel_url': reverse('custom_admin:content:tag_list')})
