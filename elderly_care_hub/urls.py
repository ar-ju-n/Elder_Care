"""
URL configuration for elderly_care_hub project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from elderly_care_hub.views import contact_view, landing
from jobs.views import admin_approve_jobs

# Import the custom admin site
from custom_admin.admin_site import admin_site

# Unregister the default admin site
admin.site = admin_site
admin.autodiscover()

urlpatterns = [
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('forum/', include('forum.urls', namespace='forum')),
    path('', landing, name='landing'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', contact_view, name='contact'),
    # Use our custom admin site
    path('djadmin/', admin_site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('content/', include('content.urls', namespace='content')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    # Custom admin URLs
    path('custom_admin/', include(('custom_admin.urls', 'custom_admin'), namespace='custom_admin')),
    path('custom_admin/jobs/approve/', admin_approve_jobs, name='admin_approve_jobs'),
    path('test/', TemplateView.as_view(template_name='test.html'), name='test'),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
