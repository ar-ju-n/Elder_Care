from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.topic_list, name='topic_list'),
    path('topic/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topic/new/', views.topic_create, name='topic_create'),
    path('topic/<int:pk>/edit/', views.topic_edit, name='topic_edit'),
    path('topic/<int:pk>/delete/', views.topic_delete, name='topic_delete'),
    path('topic/<int:pk>/reply/', views.reply_create, name='reply_create'),
    path('reply/<int:pk>/edit/', views.reply_edit, name='reply_edit'),
    path('reply/<int:pk>/delete/', views.reply_delete, name='reply_delete'),
    path('user/<int:user_id>/topics/', views.user_topics, name='user_topics'),
    path('user/<int:user_id>/replies/', views.user_replies, name='user_replies'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('api/unread_notifications_count/', views.unread_notifications_count_api, name='unread_notifications_count_api'),
    path('notifications/api/recent/', views.recent_notifications_api, name='recent_notifications_api'),
    path('notifications/api/mark_read/', views.mark_notifications_read_api, name='mark_notifications_read_api'),
]
