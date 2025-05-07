from django.urls import path
from . import views

app_name = 'eldercare_chat'

urlpatterns = [
    path('chat-list/', views.chat_list, name='chat_list'),
    path('chat/<int:assignment_id>/', views.chat_detail, name='chat_detail'),
    path('find-caregivers/', views.find_caregivers, name='find_caregivers'),
    path('request-caregiver/<int:caregiver_id>/', views.request_caregiver, name='request_caregiver'),
    path('admin/assign-caregiver/', views.assign_caregiver_view, name='assign_caregiver'),
    path('api/send-message/<int:chat_id>/', views.send_message_view, name='send_message'),
    path('api/check-messages/<int:chat_id>/', views.check_new_messages, name='check_new_messages'),
]





