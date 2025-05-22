from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

# All views and templates referenced here use only the global templates directory.
urlpatterns = [
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/api/recent/', views.notifications_api_recent, name='notifications_api_recent'),
    path('notifications/api/mark_read/', views.notifications_api_mark_read, name='notifications_api_mark_read'),
    path('messages/api/recent/', views.messages_api_recent, name='messages_api_recent'),
    path('messages/api/mark_read/', views.messages_api_mark_read, name='messages_api_mark_read'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/family/', views.family_register_view, name='family_register'),
    path('register/caregiver/', views.caregiver_register_view, name='caregiver_register'),
    path('api/check_username/', views.check_username, name='check_username'),
    path('api/check_email/', views.check_email, name='check_email'),
    path('status/', views.auth_status, name='auth_status'),
    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/update-contact/', views.update_contact, name='update_contact'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/privacy-settings/', views.privacy_settings, name='privacy_settings'),
    path('profile/notification-settings/', views.notification_settings, name='notification_settings'),
    path('profile/connected-accounts/', views.connected_accounts, name='connected_accounts'),
    path('profile/verify-email/', views.verify_email, name='verify_email'),
    path('profile/verify-email/confirm/<uidb64>/<token>/', views.verify_email_confirm, name='verify_email_confirm'),
    # 2FA URLs
    path('profile/2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('profile/2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('profile/2fa/verify/', views.verify_2fa, name='verify_2fa'),
    path('profile/2fa/backup-codes/', views.backup_codes, name='backup_codes'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/upload-picture/', views.ajax_upload_profile_picture, name='ajax_upload_profile_picture'),
    path('settings/', views.settings_view, name='settings'),
    path('emergency-contacts/', views.emergency_contacts_view, name='emergency_contacts'),
    path('medication-reminders/', views.medication_reminders_view, name='medication_reminders'),
    path('request-account-deletion/', views.request_account_deletion, name='request_account_deletion'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('cancel-account-deletion/', views.cancel_account_deletion, name='cancel_account_deletion'),
    
    # Connection requests
    path('connections/request/<int:caregiver_id>/', views.send_connection_request, name='send_connection_request'),
    path('connections/requests/', views.connection_requests, name='connection_requests'),
    path('connections/requests/<int:request_id>/<str:action>/', views.respond_to_connection_request, 
         name='respond_connection_request'),
    
    # Password change URLs for regular users
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]





