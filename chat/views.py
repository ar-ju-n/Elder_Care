import json
import os
import traceback
from datetime import datetime, timedelta

# Django imports
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import F, Q, Count, Max
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied, BadRequest, ValidationError
from django.conf import settings
from django.urls import reverse
from django.db import transaction
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.views.decorators.cache import never_cache

# Channels
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Local imports
from accounts.models import User
from .models import ChatRequest, ChatMessage
from .utils import handle_uploaded_file

@login_required
def accepted_elder_list(request):
    if not request.user.is_verified_caregiver():
        messages.error(request, 'Only verified caregivers can view this page.')
        return redirect('accounts:profile', user_id=request.user.id)
    accepted_requests = ChatRequest.objects.filter(caregiver=request.user, status='accepted').select_related('elder')
    # Gather more details and unread message count for each elder
    detailed_requests = []
    for req in accepted_requests:
        elder = req.elder
        # Count unread messages from elder to caregiver in this chat
        unread_count = ChatMessage.objects.filter(chat_request=req, sender=elder).exclude(read_by__in=[request.user]).count() if hasattr(ChatMessage, 'read_by') else 0
        detailed_requests.append({
            'request': req,
            'elder': elder,
            'bio': getattr(elder, 'bio', ''),
            'profile_picture': getattr(elder, 'profile_picture', None),
            'email': elder.email,
            'username': elder.username,
            'accepted_at': req.responded_at,
            'unread_count': unread_count,
        })
    return render(request, 'chat/accepted_elder_list.html', {'detailed_requests': detailed_requests})

@login_required
def caregiver_list(request):
    if not request.user.is_family():
        messages.error(request, 'Only family members can send chat requests.')
        return redirect('landing')
    caregivers = User.objects.filter(role=User.CAREGIVER, is_verified=True)
    caregiver_data = []
    from django.utils import timezone
    from datetime import timedelta
    for caregiver in caregivers:
        chat_request = ChatRequest.objects.filter(elder=request.user, caregiver=caregiver).first()
        # Cooldown logic
        last_request = ChatRequest.objects.filter(elder=request.user, caregiver=caregiver).order_by('-created_at').first()
        cooldown_seconds = 0
        if last_request:
            elapsed = (timezone.now() - last_request.created_at).total_seconds()
            if elapsed < 86400:
                cooldown_seconds = int(86400 - elapsed)
        if chat_request and chat_request.status == 'accepted':
            status = 'accepted'
            request_id = chat_request.id
            cooldown_seconds = 0  # No cooldown for accepted
        elif chat_request and chat_request.status == 'pending':
            status = 'pending'
            request_id = None
        else:
            status = 'none'
            request_id = None
        caregiver_data.append({
            'obj': caregiver,
            'status': status,
            'request_id': request_id,
            'cooldown_seconds': cooldown_seconds,
        })
    return render(request, 'chat/caregiver_list.html', {'caregivers': caregiver_data})

@login_required
def send_request(request, caregiver_id):
    if not request.user.is_family():
        messages.error(request, 'Only family members can send chat requests.')
        return redirect('landing')
    caregiver = get_object_or_404(User, id=caregiver_id, role=User.CAREGIVER, is_verified=True)
    # Prevent unverified caregivers from receiving chat requests
    if not caregiver.is_verified:
        messages.error(request, 'You cannot send a chat request to an unverified caregiver.')
        return redirect('chat:caregiver_list')
    # Check for last request time
    from django.utils import timezone
    from datetime import timedelta
    last_request = ChatRequest.objects.filter(elder=request.user, caregiver=caregiver).order_by('-created_at').first()
    if last_request and (timezone.now() - last_request.created_at) < timedelta(days=1):
        messages.error(request, 'You must wait 10 minutes before sending another request to this caregiver.')
        return redirect('chat:caregiver_list')
    # Create new request
    chat_request = ChatRequest.objects.create(elder=request.user, caregiver=caregiver)
    messages.success(request, 'Chat request sent!')
    # Send notification to caregiver
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{caregiver.id}',
        {
            'type': 'notification_message',
            'event': 'new_chat_request',
            'sender_name': request.user.get_full_name() or request.user.username,
        }
    )
    return redirect('chat:caregiver_list')

@login_required
def request_list(request):
    if request.user.is_caregiver():
        requests = ChatRequest.objects.filter(caregiver=request.user).order_by('-created_at')
    elif request.user.is_family():
        requests = ChatRequest.objects.filter(elder=request.user).order_by('-created_at')
    else:
        messages.error(request, 'Access denied.')
        return redirect('landing')
    return render(request, 'chat/request_list.html', {'requests': requests})

@login_required
def respond_request(request, request_id, action):
    chat_request = get_object_or_404(ChatRequest, id=request_id, caregiver=request.user, status='pending')
    if action == 'accepted':
        chat_request.status = 'accepted'
        chat_request.responded_at = timezone.now()
        chat_request.save()
        messages.success(request, 'Chat request accepted.')
        
        # Send notification to elder
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{chat_request.elder.id}',
            {
                'type': 'notification_message',
                'event': 'request_accepted',
                'accepter_name': request.user.get_full_name() or request.user.username,
                'chat_url': reverse('chat:chat_room', kwargs={'request_id': chat_request.id})
            }
        )
    elif action == 'rejected':
        chat_request.status = 'rejected'
        chat_request.responded_at = timezone.now()
        chat_request.save()
        messages.info(request, 'Chat request rejected.')
    else:
        messages.error(request, 'Invalid action.')
    return redirect('chat:request_list')

@login_required
def chat_room(request, request_id):
    # Prevent unverified caregivers from accessing chat rooms
    if request.user.is_caregiver() and not request.user.is_verified_caregiver():
        messages.error(request, 'Your caregiver account must be verified by an admin before you can access chat rooms.')
        return redirect('accounts:profile', user_id=request.user.id)
    chat_request = get_object_or_404(ChatRequest, id=request_id, status='accepted')
    
    # Ensure only participants can access the chat
    if request.user != chat_request.elder and request.user != chat_request.caregiver:
        messages.error(request, 'Access denied.')
        return redirect('landing')
    
    # Handle POST request (sending a message)
    if request.method == 'POST':
        return send_chat_message(request, chat_request)
    
    # For GET request, render the chat room
    return render_chat_room(request, chat_request)

def send_chat_message(request, chat_request):
    """Handle sending a chat message (text or file)."""
    try:
        message_text = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        
        # Validate that we have either a message or an attachment
        if not message_text and not attachment:
            return JsonResponse({'success': False, 'error': 'Message or attachment is required'}, status=400)
        
        # Handle file upload if present
        file_data = None
        if attachment:
            file_data = handle_uploaded_file(attachment, request.user.id)
            if 'error' in file_data:
                return JsonResponse({'success': False, 'error': file_data['error']}, status=400)
        
        # Create the message
        with transaction.atomic():
            message = ChatMessage.objects.create(
                chat_request=chat_request,
                sender=request.user,
                message=message_text,
                attachment=file_data['file_path'] if file_data else None,
                attachment_name=file_data.get('file_name') if file_data else None,
                is_image=file_data.get('is_image', False) if file_data else False,
                file_size=file_data.get('file_size', '0') if file_data else '0'
            )
            
            # Update the chat request's updated_at timestamp
            chat_request.updated_at = timezone.now()
            chat_request.save(update_fields=['updated_at'])
            
            # Get the other user
            other_user = chat_request.caregiver if request.user == chat_request.elder else chat_request.elder
            
            # Prepare response data
            response_data = {
                'success': True,
                'message_id': message.id,
                'message': message.message,
                'timestamp': message.timestamp.isoformat(),
                'is_read': False,
                'attachment': None
            }
            
            # Add attachment data if present
            if file_data:
                response_data['attachment'] = {
                    'url': file_data['file_url'],
                    'name': file_data['file_name'],
                    'is_image': file_data['is_image'],
                    'file_size': file_data['file_size']
                }
            
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{chat_request.id}'
            
            # Send to the chat room
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': message.message,
                    'username': request.user.username,
                    'user_id': request.user.id,
                    'user_full_name': request.user.get_full_name() or request.user.username,
                    'user_avatar': request.user.profile_picture.url if hasattr(request.user, 'profile_picture') and request.user.profile_picture else None,
                    'timestamp': message.timestamp.isoformat(),
                    'message_id': message.id,
                    'is_read': False,
                    'attachment': response_data['attachment']
                }
            )
            
            # Send notification to the other user if they're not in the chat
            notification_group = f'notifications_{other_user.id}'
            async_to_sync(channel_layer.group_send)(
                notification_group,
                {
                    'type': 'notification_message',
                    'event': 'new_message',
                    'sender_name': request.user.get_full_name() or request.user.username,
                    'message_preview': message_text[:100] + ('...' if len(message_text) > 100 else '') if message_text else 'Sent an attachment',
                    'chat_url': reverse('chat:chat_room', args=[chat_request.id])
                }
            )
            
            return JsonResponse(response_data)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def render_chat_room(request, chat_request):
    """Render the chat room template with the necessary context."""
    # Determine the other user
    other_user = chat_request.caregiver if request.user == chat_request.elder else chat_request.elder
    
    # Get messages for this chat, ordered by timestamp
    messages = ChatMessage.objects.filter(chat_request=chat_request).select_related('sender').order_by('-timestamp')[:50]
    
    # Mark messages as read
    unread_messages = messages.exclude(sender=request.user).exclude(read_by=request.user)
    if unread_messages.exists():
        # Use a single query to mark all unread messages as read
        unread_messages.update(read_by=F('read_by').bitand(~request.user.id))  # Clear the bit for this user
        unread_messages.update(read_by=F('read_by').bitor(request.user.id))    # Set the bit for this user
    
    # Get the last 50 messages (most recent first, then we'll reverse them for display)
    messages = list(reversed(messages))
    
    # Get unread count for the other user
    unread_count = ChatMessage.objects.filter(
        chat_request=chat_request,
        sender=other_user
    ).exclude(read_by=request.user).count()
    
    # Get the WebSocket URL
    ws_scheme = 'wss' if request.is_secure() else 'ws'
    ws_url = f"{ws_scheme}://{request.get_host()}/ws/chat/{chat_request.id}/"
    
    context = {
        'chat_request': chat_request,
        'other_user': other_user,
        'messages': messages,
        'ws_url': ws_url,
        'unread_count': unread_count,
        'is_elder': request.user == chat_request.elder,
        'is_caregiver': request.user == chat_request.caregiver,
        'now': timezone.now(),
        'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB in bytes
        'ALLOWED_FILE_TYPES': json.dumps([
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain'
        ])
    }
    
    return render(request, 'chat/chat_room.html', context)

@login_required
def upload_attachment(request, request_id):
    # Prevent unverified caregivers from uploading attachments
    if request.user.is_caregiver() and not request.user.is_verified_caregiver():
        return JsonResponse({'success': False, 'error': 'Your caregiver account must be verified by an admin before you can upload attachments.'})
    """Handle file uploads via AJAX"""
    if request.method != 'POST' or not request.FILES.get('attachment'):
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    
    chat_request = get_object_or_404(ChatRequest, id=request_id, status='accepted')
    
    # Ensure only participants can upload
    if request.user != chat_request.elder and request.user != chat_request.caregiver:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    attachment = request.FILES.get('attachment')
    
    # Create message with attachment
    message = ChatMessage.objects.create(
        chat_request=chat_request,
        sender=request.user,
        message='',  # Empty message for file-only uploads
        attachment=attachment
    )
    
    # Return success response with message ID
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'file_name': message.attachment_name,
        'is_image': message.is_image,
        'file_size': message.file_size_display if hasattr(message, 'file_size_display') else ''
    })

@login_required
@require_GET
def load_more_messages(request, request_id):
    """
    Load more messages for infinite scrolling.
    
    This view is called via AJAX when the user scrolls to the top of the chat.
    It returns a JSON response with older messages.
    """
    try:
        # Get the chat request
        chat_request = get_object_or_404(
            ChatRequest.objects.select_related('elder', 'caregiver').filter(
                Q(elder=request.user) | Q(caregiver=request.user),
                id=request_id
            )
        )
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = 20
        
        # Get messages for this chat, ordered by timestamp (oldest first for pagination)
        messages_qs = ChatMessage.objects.filter(
            chat_request=chat_request
        ).select_related('sender').order_by('timestamp')
        
        # Get total count for pagination
        total_messages = messages_qs.count()
        
        # Apply pagination
        paginator = Paginator(messages_qs, per_page)
        
        try:
            messages_page = paginator.page(page)
        except EmptyPage:
            return JsonResponse({
                'success': True,
                'messages': [],
                'has_more': False,
                'total_messages': total_messages,
                'total_pages': paginator.num_pages,
                'current_page': page
            })
        
        # Serialize messages
        message_list = []
        for msg in messages_page.object_list:
            message_data = {
                'id': msg.id,
                'message': msg.message,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.get_full_name() or msg.sender.username,
                'sender_avatar': msg.sender.profile_picture.url if hasattr(msg.sender, 'profile_picture') and msg.sender.profile_picture else None,
                'timestamp': msg.timestamp.isoformat(),
                'is_read': request.user in msg.read_by.all(),
                'is_sender': msg.sender == request.user
            }
            
            # Add attachment data if present
            if msg.attachment:
                message_data['attachment'] = {
                    'url': msg.attachment.url,
                    'name': msg.attachment_name or 'File',
                    'is_image': msg.is_image,
                    'file_size': msg.file_size or '0 B'
                }
            
            message_list.append(message_data)
        
        # Mark messages as read if they're from the other user
        other_user = chat_request.caregiver if request.user == chat_request.elder else chat_request.elder
        unread_messages = messages_qs.filter(
            sender=other_user,
            timestamp__lte=messages_page.object_list.last().timestamp if messages_page.object_list else timezone.now()
        ).exclude(read_by=request.user)
        
        if unread_messages.exists():
            # Mark messages as read in a single query
            unread_messages.update(read_by=F('read_by').bitor(request.user.id))
            
            # Send read receipt via WebSocket
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{chat_request.id}'
            
            # Get the most recent message ID that was just marked as read
            last_read_message = unread_messages.order_by('-timestamp').first()
            
            if last_read_message:
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'message_read',
                        'message_id': last_read_message.id,
                        'read_by': request.user.id
                    }
                )
        
        # Determine if there are more messages to load
        has_more = messages_page.has_next()
        
        return JsonResponse({
            'success': True,
            'messages': message_list,
            'has_more': has_more,
            'total_messages': total_messages,
            'total_pages': paginator.num_pages,
            'current_page': page
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def chat_list(request):
    """
    Display a list of all chat conversations for the current user.
    """
    # Get all chat requests where the user is either elder or caregiver and status is accepted
    # Annotate each ChatRequest with the latest message timestamp
    from django.db.models import Max, F, Value, DateTimeField, Case, When
    chat_requests = ChatRequest.objects.filter(
        (Q(elder=request.user) | Q(caregiver=request.user)),
        status='accepted'
    ).select_related('elder', 'caregiver')\
     .annotate(
        last_message_time=Max('messages__timestamp')
    ).annotate(
        # If there are no messages, use responded_at or created_at as fallback
        sort_time=Case(
            When(last_message_time__isnull=False, then=F('last_message_time')),
            When(responded_at__isnull=False, then=F('responded_at')),
            default=F('created_at'),
            output_field=DateTimeField()
        )
    ).order_by('-sort_time')
    
    # Annotate each chat with the last message and unread count
    chats = []
    for chat in chat_requests:
        # Get the other user
        other_user = chat.caregiver if request.user == chat.elder else chat.elder
        
        # Get the last message
        last_message = ChatMessage.objects.filter(chat_request=chat).order_by('-timestamp').first()
        
        # Count unread messages
        unread_count = ChatMessage.objects.filter(
            chat_request=chat,
            sender=other_user
        ).exclude(read_by=request.user).count()
        
        chats.append({
            'id': chat.id,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
            'last_message_time': getattr(chat, 'last_message_time', None),
            'sort_time': getattr(chat, 'sort_time', None),
        })
    
    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def start_chat(request):
    """
    Display a list of users that the current user can start a chat with.
    """
    # Get all users except the current user
    users = User.objects.exclude(id=request.user.id)
    
    # Filter based on user roles (family can only chat with caregivers and vice versa)
    if request.user.role == User.FAMILY:
        users = users.filter(role=User.CAREGIVER, is_verified=True)
    elif request.user.role == User.CAREGIVER:
        users = users.filter(role=User.FAMILY)
    else:
        # Admin or other roles can chat with anyone
        pass
    
    # Get the search query if any
    search_query = request.GET.get('q', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Order by online status and name
    users = users.order_by('-is_online', 'first_name', 'last_name', 'username')
    
    return render(request, 'chat/new_chat.html', {
        'available_users': users,
        'search_query': search_query,
    })


@login_required
def start_chat_with_user(request, user_id):
    """
    Start a new chat with a specific user.
    If a chat already exists between the users, redirect to it.
    """
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if the user is allowed to chat with the other user
    if (request.user.role == User.FAMILY and other_user.role != User.CAREGIVER) or \
       (request.user.role == User.CAREGIVER and other_user.role != User.FAMILY):
        raise PermissionDenied("You are not allowed to start a chat with this user.")
    
    # Check if a chat request already exists between these users
    chat_request = ChatRequest.objects.filter(
        (Q(elder=request.user, caregiver=other_user) | Q(elder=other_user, caregiver=request.user)),
        status='accepted'
    ).first()
    
    if chat_request:
        # Chat already exists, redirect to it
        return redirect('chat:chat_room', request_id=chat_request.id)
    
    # Create a new chat request
    if request.user.role == User.FAMILY:
        # Family members can start chats directly with caregivers
        chat_request = ChatRequest.objects.create(
            elder=request.user,
            caregiver=other_user,
            status='accepted',
            responded_at=timezone.now()
        )
        
        # Notify the other user
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{other_user.id}',
            {
                'type': 'notification_message',
                'event': 'new_chat_started',
                'sender_name': request.user.get_full_name() or request.user.username,
                'chat_url': reverse('chat:chat_room', kwargs={'request_id': chat_request.id})
            }
        )
        
        return redirect('chat:chat_room', request_id=chat_request.id)
    else:
        # Caregivers need to send a request to family members
        chat_request = ChatRequest.objects.create(
            elder=other_user,
            caregiver=request.user,
            status='pending'
        )
        
        # Notify the family member
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{other_user.id}',
            {
                'type': 'notification_message',
                'event': 'new_chat_request',
                'sender_name': request.user.get_full_name() or request.user.username,
                'request_id': chat_request.id
            }
        )
        
        messages.success(request, 'Chat request sent! The family member needs to accept it before you can start chatting.')
        return redirect('chat:chat_list')
