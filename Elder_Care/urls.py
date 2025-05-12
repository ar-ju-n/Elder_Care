from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', include('custom_admin.urls', namespace='custom_admin')),
    path('djadmin/', admin.site.urls),  # Use /djadmin/ for Django admin
    # Your other URL patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
