from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('<str:app_label>/<str:model_name>/', views.admin_list, name='admin_list'),
    path('<str:app_label>/<str:model_name>/add/', views.admin_add, name='admin_add'),
    path('<str:app_label>/<str:model_name>/<int:pk>/edit/', views.admin_edit, name='admin_edit'),
    path('<str:app_label>/<str:model_name>/<int:pk>/delete/', views.admin_delete, name='admin_delete'),
    path('<str:app_label>/<str:model_name>/bulk-delete/', views.admin_bulk_delete, name='admin_bulk_delete'),
    path('<str:app_label>/<str:model_name>/<int:pk>/view/', views.admin_view, name='admin_view'),
]
