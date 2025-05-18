from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from accounts.models import User
from .models import ChatRequest, ChatMessage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.urls import reverse

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
    
    # Handle new message submission
    if request.method == 'POST':
        msg_text = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        
        # Create message if there's text or an attachment
        if msg_text or attachment:
            ChatMessage.objects.create(
                chat_request=chat_request, 
                sender=request.user, 
                message=msg_text,
                attachment=attachment
            )
            # Redirect to avoid form resubmission
            return redirect('chat:chat_room', request_id=request_id)
    
    # Get all messages for this chat
    messages_qs = ChatMessage.objects.filter(chat_request=chat_request).order_by('timestamp')
    
    # Determine who the other user is
    other_user = chat_request.caregiver if request.user == chat_request.elder else chat_request.elder
    
    return render(request, 'chat/chat_room.html', {
        'messages': messages_qs, 
        'chat_request': chat_request, 
        'user': request.user,
        'other_user': other_user
    })

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
def load_more_messages(request, request_id):
    """Load more messages for infinite scrolling"""
    chat_request = get_object_or_404(ChatRequest, id=request_id, status='accepted')
    
    # Ensure only participants can view messages
    if request.user != chat_request.elder and request.user != chat_request.caregiver:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get page number from query params
    page = request.GET.get('page', 1)
    
    # Get messages and paginate
    messages = ChatMessage.objects.filter(chat_request=chat_request).order_by('-timestamp')
    paginator = Paginator(messages, 10)  # 10 messages per page
    
    try:
        page_obj = paginator.page(page)
    except:
        return JsonResponse({'messages': [], 'has_more': False})
    
    # Format messages for JSON response
    message_list = []
    for msg in page_obj.object_list:
        message_data = {
            'id': msg.id,
            'message': msg.message,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.username,
            'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
            'is_current_user': msg.sender == request.user,
        }
        
        if msg.attachment:
            message_data.update({
                'has_attachment': True,
                'attachment_url': msg.attachment.url,
                'attachment_name': msg.attachment.name.split('/')[-1],
                'is_image': msg.attachment.name.lower().endswith(('jpg', 'jpeg', 'png', 'gif')),
            })
        
        message_list.append(message_data)
    
    return JsonResponse({
        'messages': message_list,
        'has_more': page_obj.has_next()
    })
