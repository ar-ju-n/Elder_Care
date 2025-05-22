"""
Custom Admin Views Package

This package contains all the views for the custom admin interface,
organized into logical modules for better maintainability.
"""

# Import dashboard and auth views first to avoid circular imports
from .dashboard import dashboard
from .auth import custom_admin_login

# Import other views
from .content import *
from .users import *
from .system import *
from .reports import *
from .jobs import *
from .integrations import *
from .moderation import *
from .notifications import (
    notification_list, notification_detail, notification_create,
    notification_mark_read, notification_delete, notification_templates,
    notification_template_edit
)
from .communication import communication_oversight
from .billing import billing_controls
from .settings import *
from .events import *
# Note: event_import does not exist, so do not import or re-export it.
from .impersonation_placeholders import impersonate_user, stop_impersonation

# Re-export everything for easy importing
__all__ = [
    # Authentication
    'dashboard',
    'custom_admin_login',
    
    # Content Management
    'content_management',
    'video_list', 'video_add', 'video_edit', 'video_delete',
    'article_list', 'article_add', 'article_edit', 'article_delete',
    'link_list', 'link_add', 'link_edit', 'link_delete',
    'guide_list', 'guide_add', 'guide_edit', 'guide_delete',
    'faq_list', 'faq_add', 'faq_edit', 'faq_delete',
    'tag_list', 'tag_add', 'tag_edit', 'tag_delete',
    
    # User Management
    'user_management', 'user_import', 'export_users', 'user_roles_edit',
    'caregiver_verification_list', 'update_application_status',
    
    # System Management
    'system_status', 'system_settings', 'clear_cache', 'download_logs',
    
    # Reporting
    'reporting_dashboard', 'user_activity_report', 'content_engagement_report',
    'event_attendance_report',
    
    # Job Management
    'job_list', 'job_create', 'job_detail', 'job_edit', 'job_delete',
    'job_applications', 'update_job_application_status', 'job_analytics',
    
    # Event Management
    'event_management', 'event_list', 'event_add', 'event_edit', 
    'event_delete', 'event_attendees', 'export_events_csv',
    
    # Integration Management
    'integration_management', 'integration_list', 'integration_add', 'integration_edit', 'integration_delete',
    'integration_connect', 'integration_webhook',
    
    # Moderation APIs
    'api_moderation_messages', 'api_moderate_message',
    'api_moderation_replies', 'api_moderate_reply',
    
    # Notification Management
    'notification_list', 'notification_detail', 'notification_create',
    'notification_mark_read', 'notification_delete', 'notification_templates',
    'notification_template_edit',
    'communication_oversight',
    'billing_controls',
    'impersonate_user', 'stop_impersonation',
    
    # Event Management
    'event_management', 'event_list', 'event_add', 'event_edit', 
    'event_delete', 'event_attendees', 'export_events_csv',
    
    # Settings Management
    'general_settings', 'email_settings', 'security_settings', 'test_email',
    
    # Core Views
    'dashboard', 'custom_admin_login'
]
