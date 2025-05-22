"""
Integration Management Views for Custom Admin
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from custom_admin.models import Integration
from ..forms import AdminIntegrationForm as IntegrationForm

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
@login_required
@staff_member_required
def integration_management(request):
    """
    Main integration management view that serves as the entry point for all integration-related functionality.
    """
    # Get all integrations
    integrations = Integration.objects.all().order_by('name')
    
    # Get integration statistics
    active_integrations = integrations.filter(is_active=True).count()
    total_integrations = integrations.count()
    
    # Get recently added integrations
    recent_integrations = integrations.order_by('-created_at')[:5]
    
    context = {
        'title': 'Integration Management',
        'active_tab': 'integrations',
        'integrations': integrations,
        'active_integrations': active_integrations,
        'total_integrations': total_integrations,
        'recent_integrations': recent_integrations,
    }
    
    return TemplateResponse(
        request,
        'custom_admin/integrations/management.html',
        context
    )


def integration_list(request):
    """List all configured integrations"""
    integrations = Integration.objects.all().order_by('name')
    return render(request, 'custom_admin/integrations/integration_list.html', {
        'integrations': integrations,
        'active_tab': 'integrations',
    })

@login_required
@user_passes_test(is_admin)
def integration_add(request):
    """Add a new integration"""
    if request.method == 'POST':
        form = IntegrationForm(request.POST, request.FILES)
        if form.is_valid():
            integration = form.save(commit=False)
            
            # Handle sensitive data
            if 'api_key' in form.cleaned_data and form.cleaned_data['api_key']:
                integration.api_key = form.cleaned_data['api_key']
            if 'client_secret' in form.cleaned_data and form.cleaned_data['client_secret']:
                integration.client_secret = form.cleaned_data['client_secret']
            
            integration.save()
            messages.success(request, 'Integration added successfully.')
            return redirect('custom_admin:integration_list')
    else:
        form = IntegrationForm()
    
    return render(request, 'custom_admin/integrations/integration_form.html', {
        'form': form,
        'action': 'Add',
        'active_tab': 'integrations',
    })

@login_required
@user_passes_test(is_admin)
def integration_edit(request, integration_id):
    """Edit an existing integration"""
    integration = get_object_or_404(Integration, id=integration_id)
    
    if request.method == 'POST':
        form = IntegrationForm(request.POST, instance=integration)
        if form.is_valid():
            # Preserve sensitive data if not changed
            if 'api_key' in form.cleaned_data and not form.cleaned_data['api_key']:
                del form.cleaned_data['api_key']
            if 'client_secret' in form.cleaned_data and not form.cleaned_data['client_secret']:
                del form.cleaned_data['client_secret']
            
            integration = form.save()
            messages.success(request, 'Integration updated successfully.')
            return redirect('custom_admin:integration_list')
    else:
        form = IntegrationForm(instance=integration)
    
    return render(request, 'custom_admin/integrations/integration_form.html', {
        'form': form,
        'action': 'Edit',
        'integration': integration,
        'active_tab': 'integrations',
    })

@login_required
@user_passes_test(is_admin)
def integration_delete(request, integration_id):
    """Delete an integration"""
    integration = get_object_or_404(Integration, id=integration_id)
    
    if request.method == 'POST':
        integration.delete()
        messages.success(request, 'Integration deleted successfully.')
        return redirect('custom_admin:integration_list')
    
    return render(request, 'custom_admin/integrations/integration_confirm_delete.html', {
        'integration': integration,
        'active_tab': 'integrations',
    })

@login_required
@user_passes_test(is_admin)
def integration_connect(request, integration_id):
    """Connect to an integration"""
    integration = get_object_or_404(Integration, id=integration_id)
    
    try:
        # Implementation depends on the integration type
        if integration.integration_type == 'google_calendar':
            return _connect_google_calendar(integration)
        elif integration.integration_type == 'stripe':
            return _connect_stripe(integration)
        elif integration.integration_type == 'mailchimp':
            return _connect_mailchimp(integration)
        else:
            messages.error(request, f'Integration type {integration.integration_type} is not supported.')
    except Exception as e:
        messages.error(request, f'Error connecting to {integration.name}: {str(e)}')
    
    return redirect('custom_admin:integration_list')

def _connect_google_calendar(integration):
    """Helper method to connect to Google Calendar"""
    # Implementation for Google Calendar OAuth flow
    # This is a simplified example
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": integration.client_id,
                "client_secret": integration.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{settings.SITE_URL}/integrations/google/oauth2callback/"],
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    
    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store the state in the session for validation in the callback
    request.session['google_auth_state'] = flow.oauth2_session.state
    
    return redirect(auth_url)

def _connect_stripe(integration):
    """Helper method to connect to Stripe"""
    # Implementation for Stripe OAuth flow
    # This is a simplified example
    import stripe
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        # Create a Stripe Connect account link
        account_link = stripe.AccountLink.create(
            account=integration.external_id,
            refresh_url=f"{settings.SITE_URL}/integrations/stripe/reauth/",
            return_url=f"{settings.SITE_URL}/integrations/stripe/return/",
            type='account_onboarding',
        )
        
        return redirect(account_link.url)
    except Exception as e:
        raise Exception(f'Error connecting to Stripe: {str(e)}')

def _connect_mailchimp(integration):
    """Helper method to connect to Mailchimp"""
    # Implementation for Mailchimp OAuth flow
    # This is a simplified example
    from mailchimp_marketing import Client
    from mailchimp_marketing.api_client import ApiClientError
    
    try:
        client = Client()
        client.set_config({
            "api_key": integration.api_key,
            "server": integration.metadata.get('dc', 'us1')
        })
        
        # Test the connection
        response = client.ping.get()
        
        if response.get('health_status') == "Everything's Chimpy!":
            integration.is_active = True
            integration.save()
            messages.success(request, 'Successfully connected to Mailchimp.')
        else:
            messages.error(request, 'Failed to connect to Mailchimp.')
    except ApiClientError as e:
        raise Exception(f'Error connecting to Mailchimp: {str(e)}')

@login_required
@user_passes_test(is_admin)
def integration_webhook(request, integration_id):
    """Handle incoming webhooks for an integration"""
    integration = get_object_or_404(Integration, id=integration_id)
    
    if request.method == 'POST':
        try:
            # Verify the webhook signature if needed
            if integration.integration_type == 'stripe':
                return _handle_stripe_webhook(request, integration)
            elif integration.integration_type == 'mailchimp':
                return _handle_mailchimp_webhook(request, integration)
            else:
                return JsonResponse({'status': 'error', 'message': 'Webhook not supported'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

def _handle_stripe_webhook(request, integration):
    """Handle Stripe webhook events"""
    import stripe
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, integration.webhook_secret
        )
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Handle successful payment
            pass
        # Add more event types as needed
        
        return JsonResponse({'status': 'success'})
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)

def _handle_mailchimp_webhook(request, integration):
    """Handle Mailchimp webhook events"""
    # Verify the webhook secret if needed
    if request.GET.get('secret') != integration.webhook_secret:
        return JsonResponse({'status': 'error', 'message': 'Invalid secret'}, status=403)
    
    data = json.loads(request.body)
    event_type = data.get('type')
    
    # Handle different Mailchimp webhook events
    if event_type == 'subscribe':
        # Handle new subscription
        email = data.get('data', {}).get('email')
        # Update your database or trigger other actions
        pass
    # Add more event types as needed
    
    return JsonResponse({'status': 'success'})
