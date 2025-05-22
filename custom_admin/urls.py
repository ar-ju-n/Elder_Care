"""
URL configuration for custom_admin app.
"""
from django.urls import path, include
from django.contrib.auth.views import LogoutView

from . import views
from .views import (
    content, users, system, reports, jobs, integrations, notifications, forum
)

app_name = 'custom_admin'

# Forum Admin Moderation URL
# (Append to urlpatterns at the end, do not overwrite)

# Content Management URLs (uses only global templates/views)
content_patterns = [
    # Video URLs
    path('videos/', content.video_list, name='video_list'),
    path('videos/add/', content.video_add, name='video_add'),
    path('videos/edit/<int:video_id>/', content.video_edit, name='video_edit'),
    path('videos/delete/<int:video_id>/', content.video_delete, name='video_delete'),
    
    # Article URLs
    path('articles/', content.article_list, name='article_list'),
    path('articles/add/', content.article_add, name='article_add'),
    path('articles/edit/<int:article_id>/', content.article_edit, name='article_edit'),
    path('articles/delete/<int:article_id>/', content.article_delete, name='article_delete'),
    
    # Link URLs
    path('links/', content.link_list, name='link_list'),
    path('links/add/', content.link_add, name='link_add'),
    path('links/edit/<int:link_id>/', content.link_edit, name='link_edit'),
    path('links/delete/<int:link_id>/', content.link_delete, name='link_delete'),
    
    # Guide URLs
    path('guides/', content.guide_list, name='guide_list'),
    path('guides/add/', content.guide_add, name='guide_add'),
    path('guides/edit/<int:guide_id>/', content.guide_edit, name='guide_edit'),
    path('guides/delete/<int:guide_id>/', content.guide_delete, name='guide_delete'),
    
    # FAQ URLs
    path('faqs/', content.faq_list, name='faq_list'),
    path('faqs/add/', content.faq_add, name='faq_add'),
    path('faqs/edit/<int:faq_id>/', content.faq_edit, name='faq_edit'),
    path('faqs/delete/<int:faq_id>/', content.faq_delete, name='faq_delete'),
    
    # Tag URLs
    path('tags/', content.tag_list, name='tag_list'),
    path('tags/add/', content.tag_add, name='tag_add'),
    path('tags/edit/<int:tag_id>/', content.tag_edit, name='tag_edit'),
    path('tags/delete/<int:tag_id>/', content.tag_delete, name='tag_delete'),
]

# User Management URLs (uses only global templates/views)
user_patterns = [
    path('', users.user_management, name='user_management'),
    path('import/', users.user_import, name='user_import'),
    path('export/', users.export_users, name='export_users'),
    path('<int:user_id>/roles/', users.user_roles_edit, name='user_roles_edit'),
    path('caregiver-verifications/', users.caregiver_verification_list, name='caregiver_verification_list'),
    path('caregiver-verifications/<int:verification_id>/review/', users.caregiver_verification_review, name='caregiver_verification_review'),
    path('applications/<int:application_id>/<str:status>/', users.update_application_status, name='update_application_status'),
]

# System Management URLs (uses only global templates/views)
system_patterns = [
    path('status/', system.system_status, name='system_status'),
    path('settings/', system.system_settings, name='system_settings'),
    path('clear-cache/', system.clear_cache, name='clear_cache'),
    path('download-logs/', system.download_logs, name='download_logs'),
]

# Reporting URLs (uses only global templates/views)
report_patterns = [
    path('', reports.reporting_dashboard, name='reporting_dashboard'),
    path('user-activity/', reports.user_activity_report, name='user_activity_report'),
    path('content-engagement/', reports.content_engagement_report, name='content_engagement_report'),
    path('event-attendance/', reports.event_attendance_report, name='event_attendance_report'),
]

# Job Management URLs (uses only global templates/views)
job_patterns = [
    path('', jobs.job_list, name='job_list'),
    path('add/', jobs.job_create, name='job_add'),
    path('<int:job_id>/', jobs.job_detail, name='job_detail'),
    path('<int:job_id>/edit/', jobs.job_edit, name='job_edit'),
    path('<int:job_id>/delete/', jobs.job_delete, name='job_delete'),
    path('applications/', jobs.job_applications, name='job_applications'),
    path('applications/<int:job_id>/', jobs.job_applications, name='job_applications'),
    path('applications/detail/<int:application_id>/', jobs.application_detail, name='application_detail'),
    path('applications/update/<int:application_id>/<str:status>/', jobs.update_application_status, name='update_job_application_status'),
    path('analytics/', jobs.job_analytics, name='job_analytics'),
]

# Integration URLs (uses only global templates/views)
integration_patterns = [
    path('', integrations.integration_list, name='integration_list'),
    path('add/', integrations.integration_add, name='integration_add'),
    path('<int:integration_id>/edit/', integrations.integration_edit, name='integration_edit'),
    path('<int:integration_id>/delete/', integrations.integration_delete, name='integration_delete'),
    path('<int:integration_id>/connect/', integrations.integration_connect, name='integration_connect'),
    path('<int:integration_id>/webhook/', integrations.integration_webhook, name='integration_webhook'),
]

# Notification URLs
notification_patterns = [
    path('', notifications.notification_list, name='notification_list'),
    path('create/', notifications.notification_create, name='notification_create'),
    path('<int:notification_id>/', notifications.notification_detail, name='notification_detail'),
    path('<int:notification_id>/mark-read/', notifications.notification_mark_read, name='notification_mark_read'),
    path('<int:notification_id>/delete/', notifications.notification_delete, name='notification_delete'),
    path('templates/', notifications.notification_templates, name='notification_templates'),
    path('templates/<int:template_id>/edit/', notifications.notification_template_edit, name='notification_template_edit'),
]

# Main URL patterns
urlpatterns = [
    # Authentication
    path('login/', views.custom_admin_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='custom_admin:login'), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # App includes
    path('content_management/', content.content_management, name='content_management'),
    path('event_management/', views.event_management, name='event_management'),
    path('notification_management/', notifications.notification_management, name='notification_management'),
    path('jobs/', include((job_patterns, 'jobs'))),
    path('users/', include((user_patterns, 'users'))),
    path('system/', include((system_patterns, 'system'))),
    path('reports/', include((report_patterns, 'reports'))),
    path('integrations/', include((integration_patterns, 'integrations'))),
    path('forum_admin/', forum.admin_forum_dashboard, name='forum_admin_dashboard'),
    # Homepage Slide URLs (directly under custom_admin namespace)
    path('slides/', views.slide_list, name='slide_list'),
    path('slides/add/', views.slide_add, name='slide_add'),
    path('slides/edit/<int:slide_id>/', views.slide_edit, name='slide_edit'),
    path('slides/delete/<int:slide_id>/', views.slide_delete, name='slide_delete'),
    # Content Management URLs
    path('content/', include((content_patterns, 'content'))),
    path('notifications/', include((notification_patterns, 'notifications'))),
]

# Append the forum admin dashboard route

urlpatterns += [
    path('admin/', views.dashboard, name='admin_dashboard'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/add/', views.tag_add, name='tag_add'),
    path('tags/edit/<int:tag_id>/', views.tag_edit, name='tag_edit'),
    path('tags/delete/<int:tag_id>/', views.tag_delete, name='tag_delete'),
    path('api/moderation/messages/', views.api_moderation_messages, name='api_moderation_messages'),
    path('api/moderation/replies/', views.api_moderation_replies, name='api_moderation_replies'),
    path('api/integrations/', views.integration_list, name='integration_list'),
    path('api/integrations/add/', views.integration_add, name='integration_add'),
    path('api/integrations/<int:pk>/edit/', views.integration_edit, name='integration_edit'),
    path('api/download_logs/', views.download_logs, name='download_logs'),
    path('api/clear_cache/', views.clear_cache, name='clear_cache'),
    path('api/backup_database/', views.backup_database, name='backup_database'),
    path('api/restore_database/', views.restore_database, name='restore_database'),
    path('jobs/', views.job_list, name='job_list'),
path('notifications/', views.notification_list, name='notification_list'),
path('jobs/add/', views.job_create, name='job_add'),
    # System settings
    path('settings/general/', views.general_settings, name='general_settings'),
    path('settings/email/', views.email_settings, name='email_settings'),
    path('settings/security/', views.security_settings, name='security_settings'),
    # Maintenance
    path('maintenance/clear-cache/', views.clear_cache, name='clear_cache'),
    path('maintenance/optimize-db/', views.optimize_database, name='optimize_database'),
    path('maintenance/update-check/', views.check_for_updates, name='check_updates'),
    path('', views.dashboard, name='dashboard'),
    path('integrations/', views.integration_management, name='integration_management'),
    path('maintenance/', views.maintenance_management, name='maintenance_management'),
    path('content/', views.content_management, name='content_management'),
    path('events/', views.event_management, name='event_management'),
    path('events/export/', views.export_events_csv, name='export_events_csv'),
    path('notifications/', include((notification_patterns, 'notifications'))),
    path('reporting/', reports.reporting_dashboard, name='reporting_dashboard'),
    path('communication/', views.communication_oversight, name='communication_oversight'),
    path('billing/', views.billing_controls, name='billing_controls'),

]
