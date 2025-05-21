from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import ApplicationDetailView

app_name = 'jobs'

urlpatterns = [
    # Job listing and detail views
    path('', views.job_list, name='job_list'),
    path('find-caregivers/', views.job_list, name='find_caregivers'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    
    # Job CRUD operations
    path('post/', views.JobCreateView.as_view(), name='post_job'),
    path('<int:job_id>/update/', views.JobUpdateView.as_view(), name='update_job'),
    path('<int:job_id>/delete/', views.JobDeleteView.as_view(), name='delete_job'),
    
    # Application related URLs
    path('apply/<int:job_id>/', views.apply_job_view, name='apply_job'),
    path('application/<int:application_id>/', ApplicationDetailView.as_view(), name='application_detail'),
    path('application/<int:application_id>/update-status/', 
         views.update_application_status, 
         name='update_application_status'),
    path('application/<int:application_id>/delete/', 
         views.delete_application, 
         name='delete_application'),
    
    # Admin specific URLs
    path('admin/approve/', views.admin_approve_jobs, name='admin_approve_jobs'),
    path('<int:job_id>/assign-caregiver/', views.assign_caregiver_view, name='assign_caregiver'),
    
    # Job status updates
    path('<int:job_id>/update-status/', views.update_job_status, name='update_job_status'),
    
    # Success/confirmation pages
    path('success/', TemplateView.as_view(template_name='jobs/success.html'), name='success'),
]

