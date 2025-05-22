"""
Reporting Views for Custom Admin
"""
import csv
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q, F, Sum, Avg, DateTimeField, IntegerField
from django.db.models.functions import TruncDate, TruncHour, TruncDay, TruncWeek, TruncMonth
from django.utils import timezone

from accounts.models import User
from events.models import Event
from forum.models import Topic, Reply
from content.models import Article, Video, Link
from jobs.models import Job, Application

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def reporting_dashboard(request):
    """Main reporting dashboard"""
    # Date ranges for reports
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # User statistics
    user_stats = {
        'total': User.objects.count(),
        'new_this_month': User.objects.filter(
            date_joined__gte=timezone.now().replace(day=1)
        ).count(),
        'active': User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'by_role': User.objects.values('role').annotate(
            count=Count('id')
        ).order_by('-count'),
    }
    
    # Content statistics
    content_stats = {
        'articles': Article.objects.count(),
        'videos': Video.objects.count(),
        'links': Link.objects.count(),
        'posts': Post.objects.count(),
        'replies': Reply.objects.count(),
        'jobs': Job.objects.count(),
        'events': Event.objects.count(),
    }
    
    # Engagement metrics
    engagement_stats = {
        'avg_posts_per_user': Post.objects.aggregate(
            avg=Avg(Count('author', distinct=True))
        )['avg'] or 0,
        'avg_replies_per_post': Reply.objects.aggregate(
            avg=Avg(Count('post', distinct=True))
        )['avg'] or 0,
        'event_registrations': EventRegistration.objects.count(),
        'job_applications': JobApplication.objects.count(),
    }
    
    # Recent activities
    recent_activities = {
        'new_users': User.objects.order_by('-date_joined')[:5],
        'recent_posts': Post.objects.select_related('author').order_by('-created_at')[:5],
        'upcoming_events': Event.objects.filter(
            start_time__gte=timezone.now()
        ).order_by('start_time')[:5],
    }
    
    context = {
        'user_stats': user_stats,
        'content_stats': content_stats,
        'engagement_stats': engagement_stats,
        'recent_activities': recent_activities,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'active_tab': 'reports',
    }
    
    return render(request, 'custom_admin/reports/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def user_activity_report(request):
    """Generate user activity report"""
    # Get date range from request or use default (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            pass
    
    # Get user activity data
    user_activity = User.objects.annotate(
        post_count=Count('posts', filter=Q(posts__created_at__range=(start_date, end_date))),
        reply_count=Count('replies', filter=Q(replies__created_at__range=(start_date, end_date))),
        event_count=Count('event_registrations', filter=Q(event_registrations__created_at__range=(start_date, end_date))),
        job_application_count=Count('job_applications', filter=Q(job_applications__created_at__range=(start_date, end_date))),
        last_activity=Max('last_login')
    ).order_by('-last_login')
    
    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=user_activity_{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        writer.writerow([
            'User ID', 'Email', 'Name', 'Role', 'Last Login', 
            'Posts', 'Replies', 'Events', 'Job Applications'
        ])
        
        for user in user_activity:
            writer.writerow([
                user.id,
                user.email,
                user.get_full_name(),
                user.get_role_display(),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                user.post_count,
                user.reply_count,
                user.event_count,
                user.job_application_count
            ])
        
        return response
    
    context = {
        'user_activity': user_activity,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'active_tab': 'reports',
    }
    
    return render(request, 'custom_admin/reports/user_activity.html', context)

@login_required
@user_passes_test(is_admin)
def content_engagement_report(request):
    """Generate content engagement report"""
    # Get date range from request or use default (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            pass
    
    # Get content engagement data
    content_stats = {
        'top_posts': Post.objects.annotate(
            like_count=Count('likes'),
            reply_count=Count('replies')
        ).filter(
            created_at__range=(start_date, end_date)
        ).order_by('-like_count', '-reply_count')[:10],
        
        'top_videos': Video.objects.annotate(
            view_count=Count('views')
        ).filter(
            created_at__range=(start_date, end_date)
        ).order_by('-view_count')[:10],
        
        'content_by_type': [
            {'type': 'Articles', 'count': Article.objects.filter(created_at__range=(start_date, end_date)).count()},
            {'type': 'Videos', 'count': Video.objects.filter(created_at__range=(start_date, end_date)).count()},
            {'type': 'Links', 'count': Link.objects.filter(created_at__range=(start_date, end_date)).count()},
            {'type': 'Forum Posts', 'count': Post.objects.filter(created_at__range=(start_date, end_date)).count()},
        ],
    }
    
    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=content_engagement_{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        
        # Write content type summary
        writer.writerow(['Content Type', 'Count'])
        for item in content_stats['content_by_type']:
            writer.writerow([item['type'], item['count']])
        
        # Write top posts
        writer.writerow([])
        writer.writerow(['Top Posts', 'Likes', 'Replies'])
        for post in content_stats['top_posts']:
            writer.writerow([post.title, post.like_count, post.reply_count])
        
        # Write top videos
        writer.writerow([])
        writer.writerow(['Top Videos', 'Views'])
        for video in content_stats['top_videos']:
            writer.writerow([video.title, video.view_count])
        
        return response
    
    context = {
        'content_stats': content_stats,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'active_tab': 'reports',
    }
    
    return render(request, 'custom_admin/reports/content_engagement.html', context)

@login_required
@user_passes_test(is_admin)
def event_attendance_report(request):
    """Generate event attendance report"""
    # Get date range from request or use default (last 90 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            pass
    
    # Get event data
    events = Event.objects.filter(
        start_time__range=(start_date, end_date)
    ).annotate(
        registration_count=Count('registrations'),
        attendance_count=Count('registrations', filter=Q(registrations__attended=True))
    ).order_by('-start_time')
    
    # Calculate summary statistics
    summary = {
        'total_events': events.count(),
        'total_registrations': sum(e.registration_count for e in events),
        'total_attendance': sum(e.attendance_count for e in events),
        'avg_attendance_rate': (sum(
            (e.attendance_count / e.registration_count * 100) 
            for e in events if e.registration_count > 0
        ) / events.count()) if events.count() > 0 else 0,
    }
    
    # Export to CSV if requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=event_attendance_{datetime.now().strftime("%Y%m%d")}.csv'
        
        writer = csv.writer(response)
        writer.writerow([
            'Event ID', 'Title', 'Start Time', 'End Time', 
            'Registrations', 'Attendees', 'Attendance Rate'
        ])
        
        for event in events:
            attendance_rate = (event.attendance_count / event.registration_count * 100) if event.registration_count > 0 else 0
            writer.writerow([
                event.id,
                event.title,
                event.start_time.strftime('%Y-%m-%d %H:%M'),
                event.end_time.strftime('%Y-%m-%d %H:%M'),
                event.registration_count,
                event.attendance_count,
                f"{attendance_rate:.1f}%"
            ])
        
        return response
    
    context = {
        'events': events,
        'summary': summary,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'active_tab': 'reports',
    }
    
    return render(request, 'custom_admin/reports/event_attendance.html', context)
