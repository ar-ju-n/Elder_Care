from django.http import HttpResponseForbidden
from django.urls import resolve
from django.conf import settings
from django.shortcuts import redirect

class RoleBasedAccessMiddleware:
    """
    Middleware to handle role-based access control (RBAC) for the application.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Define URL patterns that are accessible to all authenticated users
        self.allowed_for_all = [
            'home',
            'profile',
            'profile_update',
            'password_change',
            'password_change_done',
            'logout',
        ]
        
        # Define admin-only URL names
        self.admin_urls = [
            'admin:index',
            'admin_user_list',
            'admin_user_detail',
            'admin_user_edit',
            'admin_job_list',
            'admin_job_detail',
            'admin_article_list',
            'admin_article_create',
            'admin_article_edit',
            'admin_video_list',
            'admin_video_create',
            'admin_video_edit',
            'admin_link_list',
            'admin_link_create',
            'admin_link_edit',
            'admin_homepageslide_list',
            'admin_homepageslide_create',
            'admin_homepageslide_edit',
            'admin_guide_list',
            'admin_guide_create',
            'admin_guide_edit',
            'admin_faq_list',
            'admin_faq_create',
            'admin_faq_edit',
            'admin_caregiver_list',
            'admin_caregiver_detail',
            'admin_caregiver_approve',
            'admin_caregiver_decline',
            'admin_event_list',
            'admin_event_detail',
            'admin_forum_list',
            'admin_forum_detail',
        ]
        
        # Define family member URL names
        self.family_urls = [
            'job_create',
            'job_edit',
            'job_delete',
            'forum_create',
            'forum_edit',
            'forum_delete',
            'event_create',
            'event_edit',
            'event_delete',
            'send_chat_request',
            'chatbot',
        ]
        
        # Define caregiver URL names
        self.caregiver_urls = [
            'job_apply',
            'job_applications',
            'forum_participate',
            'event_register',
            'event_participate',
        ]

    def __call__(self, request):
        # Get the current URL name
        try:
            current_url_name = resolve(request.path_info).url_name
            if request.resolver_match.namespace:
                current_url_name = f"{request.resolver_match.namespace}:{current_url_name}"
        except:
            current_url_name = ''
        
        # Skip middleware for unauthenticated users (handled by login_required)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Allow access to allowed_for_all URLs for all authenticated users
        if current_url_name in self.allowed_for_all:
            return self.get_response(request)
        
        # Check admin access
        if current_url_name in self.admin_urls and not request.user.role == 'admin':
            return HttpResponseForbidden("You don't have permission to access this page.")
        
        # Check family member access
        if current_url_name in self.family_urls and not request.user.role == 'family':
            return HttpResponseForbidden("You don't have permission to access this page.")
        
        # Check caregiver access
        if current_url_name in self.caregiver_urls and not request.user.role == 'caregiver':
            return HttpResponseForbidden("You don't have permission to access this page.")
        
        # Allow access to public URLs
        return self.get_response(request)
