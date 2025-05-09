from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('caregivers/', views.caregiver_list, name='caregiver_list'),
    path('send_request/<int:caregiver_id>/', views.send_request, name='send_request'),
    path('requests/', views.request_list, name='request_list'),
    path('accepted/', views.accepted_elder_list, name='accepted_elder_list'),
    path('respond_request/<int:request_id>/<str:action>/', views.respond_request, name='respond_request'),
    path('room/<int:request_id>/', views.chat_room, name='chat_room'),
    path('room/<int:request_id>/upload/', views.upload_attachment, name='upload_attachment'),
    path('room/<int:request_id>/load-more/', views.load_more_messages, name='load_more_messages'),
]


