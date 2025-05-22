from django.urls import path
from django.views.generic import TemplateView
from . import views
from .video_views import (
    VideoListView, VideoDetailView, VideoCreateView,
    VideoUpdateView, VideoDeleteView, toggle_video_status
)

app_name = 'content'

# All views and templates referenced here use only the global templates directory.
urlpatterns = [
    # Article URLs (kept for backward compatibility, update later)
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/edit/', views.article_edit, name='article_edit'),
    path('articles/publish/', views.publish_article_view, name='publish_article'),
    
    # Video URLs
    path('videos/', VideoListView.as_view(), name='video_list'),
    path('videos/add/', VideoCreateView.as_view(), name='video_create'),
    path('videos/<int:pk>/', VideoDetailView.as_view(), name='video_detail'),
    path('videos/<int:pk>/edit/', VideoUpdateView.as_view(), name='video_update'),
    path('videos/<int:pk>/delete/', VideoDeleteView.as_view(), name='video_delete'),
    path('videos/<int:pk>/toggle/', toggle_video_status, name='video_toggle'),
    
    # Deprecated video URLs (kept for backward compatibility)
    path('videos/publish/', views.publish_video_view, name='publish_video'),
]
