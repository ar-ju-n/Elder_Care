from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:pk>/rsvp/', views.event_rsvp, name='event_rsvp'),
]
