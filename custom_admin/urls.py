from django.urls import path, re_path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    re_path(r'^admin/?$', views.admin_login, name='admin_login'),  # /admin and /admin/ both work
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),  # dashboard after login
    path('admin/activity/', views.admin_dashboard, name='recent_activity'),  # recent activity page
    path('admin/<str:app_label>/<str:model_name>/', views.admin_list, name='admin_list'),
    path('admin/<str:app_label>/<str:model_name>/add/', views.admin_add, name='admin_add'),
    path('admin/<str:app_label>/<str:model_name>/<int:pk>/edit/', views.admin_edit, name='admin_edit'),
    path('admin/<str:app_label>/<str:model_name>/<int:pk>/delete/', views.admin_delete, name='admin_delete'),
    path('admin/<str:app_label>/<str:model_name>/bulk-delete/', views.admin_bulk_delete, name='admin_bulk_delete'),
    path('admin/<str:app_label>/<str:model_name>/<int:pk>/view/', views.admin_view, name='admin_view'),
]

