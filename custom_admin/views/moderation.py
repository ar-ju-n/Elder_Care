"""
Moderation API Views for Custom Admin
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_moderation_messages(request):
    """
    API endpoint to get messages that need moderation
    """
    try:
        # Get query parameters
        status = request.GET.get('status', 'pending')  # pending, approved, rejected
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Base query - you'll need to adjust this based on your Message model
        from messaging.models import Message  # Import here to avoid circular imports
        
        messages = Message.objects.filter(
            moderation_status=status.upper()
        ).order_by('-created_at')
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_messages = messages[start:end]
        
        # Format response
        response_data = {
            'status': 'success',
            'count': messages.count(),
            'page': page,
            'per_page': per_page,
            'results': [
                {
                    'id': msg.id,
                    'content': msg.content,
                    'author': str(msg.author),
                    'created_at': msg.created_at.isoformat(),
                    'status': msg.moderation_status,
                }
                for msg in paginated_messages
            ]
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_moderate_message(request, message_id):
    """
    API endpoint to moderate a message
    """
    try:
        from messaging.models import Message  # Import here to avoid circular imports
        
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'reject'
        
        if action not in ['approve', 'reject']:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid action'},
                status=400
            )
        
        message = get_object_or_404(Message, id=message_id)
        
        if action == 'approve':
            message.moderation_status = 'APPROVED'
            message.is_published = True
            message.save()
            
            # Trigger any post-approval actions
            # e.g., notify the author, update related objects, etc.
            
            return JsonResponse({
                'status': 'success',
                'message': 'Message approved successfully',
                'new_status': 'APPROVED'
            })
            
        elif action == 'reject':
            message.moderation_status = 'REJECTED'
            message.is_published = False
            message.save()
            
            # Trigger any post-rejection actions
            # e.g., notify the author, log the action, etc.
            
            return JsonResponse({
                'status': 'success',
                'message': 'Message rejected successfully',
                'new_status': 'REJECTED'
            })
            
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def api_moderation_replies(request):
    """
    API endpoint to get replies that need moderation
    """
    try:
        # Get query parameters
        status = request.GET.get('status', 'pending')  # pending, approved, rejected
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Base query - you'll need to adjust this based on your Reply model
        from messaging.models import Reply  # Import here to avoid circular imports
        
        replies = Reply.objects.filter(
            moderation_status=status.upper()
        ).order_by('-created_at')
        
        # Apply pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_replies = replies[start:end]
        
        # Format response
        response_data = {
            'status': 'success',
            'count': replies.count(),
            'page': page,
            'per_page': per_page,
            'results': [
                {
                    'id': reply.id,
                    'content': reply.content,
                    'author': str(reply.author),
                    'message_id': reply.message.id,
                    'created_at': reply.created_at.isoformat(),
                    'status': reply.moderation_status,
                }
                for reply in paginated_replies
            ]
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def api_moderate_reply(request, reply_id):
    """
    API endpoint to moderate a reply
    """
    try:
        from messaging.models import Reply  # Import here to avoid circular imports
        
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'reject'
        
        if action not in ['approve', 'reject']:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid action'},
                status=400
            )
        
        reply = get_object_or_404(Reply, id=reply_id)
        
        if action == 'approve':
            reply.moderation_status = 'APPROVED'
            reply.is_published = True
            reply.save()
            
            # Trigger any post-approval actions
            # e.g., notify the author, update related objects, etc.
            
            return JsonResponse({
                'status': 'success',
                'message': 'Reply approved successfully',
                'new_status': 'APPROVED'
            })
            
        elif action == 'reject':
            reply.moderation_status = 'REJECTED'
            reply.is_published = False
            reply.save()
            
            # Trigger any post-rejection actions
            # e.g., notify the author, log the action, etc.
            
            return JsonResponse({
                'status': 'success',
                'message': 'Reply rejected successfully',
                'new_status': 'REJECTED'
            })
            
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=400
        )
