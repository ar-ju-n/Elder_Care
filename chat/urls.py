from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'chat'

# All views and templates referenced here use only the global templates directory.
urlpatterns = [
    # Redirect root to chat list
    path('', RedirectView.as_view(pattern_name='chat:chat_list', permanent=False), name='index'),
    
    # Chat list and management
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/new/', views.start_chat, name='start_chat'),
    path('chats/start/<int:user_id>/', views.start_chat_with_user, name='start_chat_with_user'),
    
    # Chat room and messages
    path('room/<int:request_id>/', views.chat_room, name='chat_room'),
    path('room/<int:request_id>/upload/', views.upload_attachment, name='upload_attachment'),
    path('room/<int:request_id>/load-more/', views.load_more_messages, name='load_more_messages'),
    
    # Chat requests (legacy)
    path('caregivers/', views.caregiver_list, name='caregiver_list'),
    path('send_request/<int:caregiver_id>/', views.send_request, name='send_request'),
    path('requests/', views.request_list, name='request_list'),
    path('accepted/', views.accepted_elder_list, name='accepted_elder_list'),
    path('respond_request/<int:request_id>/<str:action>/', views.respond_request, name='respond_request'),
]
