"""
URL configuration for elderly_care_hub project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from elderly_care_hub.views import contact_view, landing

from custom_admin.views import admin_login

urlpatterns = [
    path('events/', include('events.urls')),
    path('forum/', include('forum.urls', namespace='forum')),
    path('admin', admin_login, name='custom_admin_login_noslash'),  # /admin (no slash)
    path('admin/', admin_login, name='custom_admin_login'),         # /admin/ (slash)
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),  # /admin/... for all other admin URLs
    path('', landing, name='landing'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', contact_view, name='contact'),
    path('djadmin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('content/', include('content.urls', namespace='content')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
]

# Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
