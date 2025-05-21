from django.shortcuts import render

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Topic, Reply
from django.utils import timezone

# List all topics (with optional category filter)
def topic_list(request):
    from .models import Category
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    if category_id:
        topics = Topic.objects.filter(category_id=category_id).order_by('-created_at')
        selected_category = Category.objects.filter(id=category_id).first()
    else:
        topics = Topic.objects.order_by('-created_at')
        selected_category = None
    return render(request, 'forum/topic_list.html', {'topics': topics, 'categories': categories, 'selected_category': selected_category})

# Show topic detail and replies
from .models import ReplyUpvote

def topic_detail(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    replies = topic.replies.order_by('created_at')
    user_upvoted_reply_ids = set()
    if request.user.is_authenticated:
        user_upvoted_reply_ids = set(ReplyUpvote.objects.filter(user=request.user, reply__in=replies).values_list('reply_id', flat=True))
    # Handle upvote and best answer actions
    if request.method == 'POST':
        action = request.POST.get('action')
        reply_id = request.POST.get('reply_id')
        if action == 'upvote' and request.user.is_authenticated:
            reply = get_object_or_404(Reply, id=reply_id)
            # Prevent self-upvoting
            if reply.author != request.user:
                upvote, created = ReplyUpvote.objects.get_or_create(reply=reply, user=request.user)
                if not created:
                    # Already upvoted, so remove upvote (toggle off)
                    upvote.delete()
            return redirect('forum:topic_detail', pk=pk)
        elif action == 'best_answer' and request.user.is_authenticated:
            reply = get_object_or_404(Reply, id=reply_id)
            # Only topic author or staff can mark best answer
            if (request.user == topic.author or request.user.is_staff):
                # Unmark any previous best answer
                topic.replies.filter(is_best_answer=True).update(is_best_answer=False)
                reply.is_best_answer = True
                reply.save()
                # Notify reply author (if not the same as marker)
                from .models import Notification
                if reply.author != request.user:
                    notif = Notification.objects.create(
                        user=reply.author,
                        message=f"Your reply was marked as the Best Answer in: {topic.title}",
                        url=request.build_absolute_uri(),
                        notif_type='best_answer',
                    )
                    from forum.models import broadcast_notification
                    from .models import Notification as NotifModel
                    unread_count = NotifModel.objects.filter(user=reply.author, is_read=False).count()
                    broadcast_notification(reply.author.id, unread_count)
            return redirect('forum:topic_detail', pk=pk)
    # Prepare reply info
    reply_infos = []
    for reply in replies:
        reply_infos.append({
            'obj': reply,
            'upvotes': reply.upvotes.count(),
            'is_best_answer': reply.is_best_answer,
            'user_has_upvoted': reply.id in user_upvoted_reply_ids,
        })
    return render(request, 'forum/topic_detail.html', {
        'topic': topic,
        'reply_infos': reply_infos,
        'replies': replies,  # for backward compatibility
    })

# Create new topic
from .models import Category

@login_required
def topic_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        category_id = request.POST.get('category')
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if title and body and category:
            Topic.objects.create(title=title, body=body, author=request.user, category=category)
            return redirect('forum:topic_list')
        # If invalid, re-render with error
        return render(request, 'forum/topic_form.html', {'categories': categories, 'title': title, 'body': body, 'category_id': category_id})
    return render(request, 'forum/topic_form.html', {'categories': categories})

# Add a reply to a topic
@login_required
def reply_create(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            reply = Reply.objects.create(topic=topic, body=body, author=request.user)
            from django.core.mail import send_mail
            from django.urls import reverse
            from django.conf import settings
            import re
            from .models import Notification
            from forum.models import broadcast_notification
            from .models import Notification as NotifModel
            from django.contrib.auth import get_user_model
            User = get_user_model()
            notified_users = set()

            # 1. In-app notification to topic author (for reply)
            if topic.author != request.user:
                Notification.objects.create(
                    user=topic.author,
                    message=f"{request.user.get_full_name() or request.user.username} replied to your topic: {topic.title}",
                    url=reverse('forum:topic_detail', args=[topic.pk]),
                    notif_type='reply',
                )
                unread_count = NotifModel.objects.filter(user=topic.author, is_read=False).count()
                broadcast_notification(topic.author.id, unread_count)

            # 2. Email notification to topic author (if not replier and opted-in)
            profile = getattr(topic.author, 'profile', None)
            if topic.author != request.user and topic.author.email and (not profile or getattr(profile, 'forum_email_notifications', True)):
                subject = f"New reply to your topic: {topic.title}"
                topic_url = request.build_absolute_uri(reverse('forum:topic_detail', args=[topic.pk]))
                message = f"Hi {topic.author.username},\n\n" \
                          f"{request.user.get_full_name() or request.user.username} has replied to your forum topic: {topic.title}.\n\n" \
                          f"Read it here: {topic_url}\n\n" \
                          f"---\nElder Care & Mindful Support Hub"
                send_mail(
                    subject,
                    message,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                    [topic.author.email],
                    fail_silently=True
                )
                notified_users.add(topic.author.username)

            # 3. Mention notification (in-app and email) for @username in reply body
            mentioned_usernames = set(re.findall(r'@([\w.-]+)', body or ''))
            for username in mentioned_usernames:
                try:
                    user = User.objects.get(username=username)
                    if user.username in [request.user.username, topic.author.username]:
                        continue
                    # In-app notification for mention
                    Notification.objects.create(
                        user=user,
                        message=f"{request.user.get_full_name() or request.user.username} mentioned you in a reply to: {topic.title}",
                        url=reverse('forum:topic_detail', args=[topic.pk]),
                        notif_type='mention',
                    )
                    unread_count = NotifModel.objects.filter(user=user, is_read=False).count()
                    broadcast_notification(user.id, unread_count)
                    profile = getattr(user, 'profile', None)
                    if user.email and (not profile or getattr(profile, 'forum_email_notifications', True)):
                        subject = f"You were mentioned in a forum reply"
                        topic_url = request.build_absolute_uri(reverse('forum:topic_detail', args=[topic.pk]))
                        message = f"Hi {user.username},\n\n" \
                                  f"{request.user.get_full_name() or request.user.username} mentioned you in a reply to the topic: {topic.title}.\n\n" \
                                  f"Read it here: {topic_url}\n\n" \
                                  f"---\nElder Care & Mindful Support Hub"
                        send_mail(
                            subject,
                            message,
                            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                            [user.email],
                            fail_silently=True
                        )
                except User.DoesNotExist:
                    continue

    return redirect('forum:topic_detail', pk=pk)

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

# List all topics by user
def user_topics(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    topics = user.forum_topics.order_by('-created_at')
    paginator = Paginator(topics, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'forum/user_topics.html', {'profile_user': user, 'page_obj': page_obj})

# List all replies by user
def user_replies(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    replies = user.forum_replies.order_by('-created_at')
    paginator = Paginator(replies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'forum/user_replies.html', {'profile_user': user, 'page_obj': page_obj})

from .models import Notification

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from core.models import Notification as CoreNotification
from .models import Notification as ForumNotification

@login_required
def notifications_list(request):
    # Fetch both forum and core notifications for the logged-in user
    forum_notifications = list(ForumNotification.objects.filter(user=request.user))
    core_notifications = list(CoreNotification.objects.filter(recipient=request.user))

    # Normalize both to a common dict format
    def notif_to_dict(n, source):
        return {
            'id': n.id,
            'message': getattr(n, 'message', getattr(n, 'subject', '')),
            'url': getattr(n, 'url', '#'),
            'is_read': n.is_read,
            'created_at': n.created_at,
            'notif_type': getattr(n, 'notif_type', source),
            'source': source,
            'obj': n,
        }
    all_notifications = [notif_to_dict(n, 'forum') for n in forum_notifications] + [notif_to_dict(n, 'core') for n in core_notifications]
    # Sort by created_at descending
    all_notifications.sort(key=lambda n: n['created_at'], reverse=True)

    # Paginate
    from django.core.paginator import Paginator
    paginator = Paginator(all_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Mark all as read if requested
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        ForumNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        CoreNotification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'forum/notifications_list.html', {'page_obj': page_obj})

from django.http import JsonResponse
from django.core import serializers
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

@login_required
def unread_notifications_count_api(request):
    from .models import Notification
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})

@login_required
def recent_notifications_api(request):
    from .models import Notification
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    data = [
        {
            'id': n.id,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': timesince(n.created_at) + ' ago',
            'notif_type': n.notif_type,
        } for n in qs
    ]
    return JsonResponse({'notifications': data})

@login_required
@require_POST
def mark_notifications_read_api(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

# Edit a topic
@login_required
def topic_edit(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    categories = Category.objects.all()
    if not (request.user == topic.author or request.user.is_staff):
        return redirect('forum:topic_detail', pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        category_id = request.POST.get('category')
        category = Category.objects.filter(id=category_id).first() if category_id else None
        if title and body and category:
            topic.title = title
            topic.body = body
            topic.category = category
            topic.save()
            return redirect('forum:topic_detail', pk=pk)
        # If invalid, re-render with error
        return render(request, 'forum/topic_form.html', {'topic': topic, 'edit_mode': True, 'categories': categories})
    return render(request, 'forum/topic_form.html', {'topic': topic, 'edit_mode': True, 'categories': categories})

# Delete a topic
@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if not (request.user == topic.author or request.user.is_staff):
        return redirect('forum:topic_detail', pk=pk)
    if request.method == 'POST':
        topic.delete()
        return redirect('forum:topic_list')
    return render(request, 'forum/topic_confirm_delete.html', {'topic': topic})

# Edit a reply
@login_required
def reply_edit(request, pk):
    reply = get_object_or_404(Reply, pk=pk)
    if not (request.user == reply.author or request.user.is_staff):
        return redirect('forum:topic_detail', pk=reply.topic.pk)
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            reply.body = body
            reply.save()
            return redirect('forum:topic_detail', pk=reply.topic.pk)
    return render(request, 'forum/reply_form.html', {'reply': reply, 'edit_mode': True})

# Delete a reply
@login_required
def reply_delete(request, pk):
    reply = get_object_or_404(Reply, pk=pk)
    topic_pk = reply.topic.pk
    if not (request.user == reply.author or request.user.is_staff):
        return redirect('forum:topic_detail', pk=topic_pk)
    if request.method == 'POST':
        reply.delete()
        return redirect('forum:topic_detail', pk=topic_pk)
    return render(request, 'forum/reply_confirm_delete.html', {'reply': reply})
