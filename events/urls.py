from django.urls import path
from . import views

app_name = 'events'

# All views and templates referenced here use only the global templates directory.
urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('create/', views.event_create, name='event_create'),
    path('<int:pk>/', views.event_detail, name='event_detail'),
    path('<int:pk>/rsvp/', views.event_rsvp, name='event_rsvp'),
]
