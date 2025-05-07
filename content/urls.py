from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/publish/', views.publish_article_view, name='publish_article'),
    path('videos/', views.video_list, name='video_list'),
    path('videos/<int:pk>/', views.video_detail, name='video_detail'),
    path('videos/publish/', views.publish_video_view, name='publish_video'),
]
