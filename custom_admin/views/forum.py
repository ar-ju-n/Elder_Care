from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from forum.models import Topic, Category, Reply
from django.contrib import messages

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_forum_dashboard(request):
    topics = Topic.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    replies = Reply.objects.all().order_by('-created_at')
    return render(request, 'custom_admin/forum_admin_dashboard.html', {
        'topics': topics,
        'categories': categories,
        'replies': replies,
    })
