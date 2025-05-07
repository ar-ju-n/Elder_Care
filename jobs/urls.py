from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('find-caregivers/', views.job_list, name='find_caregivers'),  # Same view, different template
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('post/', views.post_job_view, name='post_job'),
    path('apply/<int:job_id>/', views.apply_job_view, name='apply_job'),
    path('application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
]

