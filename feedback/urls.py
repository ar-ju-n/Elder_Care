from django.urls import path
from . import views

app_name = 'feedback'

# All views and templates referenced here use only the global templates directory.
urlpatterns = [
    path('', views.feedback_list, name='feedback_list'),
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('moderate/', views.moderate_feedback, name='moderate_feedback'),
]
