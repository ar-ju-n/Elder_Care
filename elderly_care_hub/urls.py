"""
URL configuration for elderly_care_hub project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('custom_admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('djadmin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('chat/', include('eldercare_chat.urls', namespace='eldercare_chat')),
    path('content/', include('content.urls', namespace='content')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
]

# Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
