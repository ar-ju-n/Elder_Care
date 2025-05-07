from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('content/', include('content.urls', namespace='content')),
    path('feedback/', include('feedback.urls', namespace='feedback')),
    path('chat/', include('eldercare_chat.urls', namespace='chat')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    path('', include('content.urls')),  # Default to content app for homepage
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)