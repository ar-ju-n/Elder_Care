from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Assignment, Chat, Message
from .services import assign_caregiver_to_elderly, create_chat, send_message
from accounts.models import User

# Helpers
def is_elderly(user):
    return user.is_authenticated and user.is_elderly()
def is_caregiver(user):
    return user.is_authenticated and user.is_caregiver()
def is_admin(user):
    return user.is_authenticated and user.is_admin_role()

@login_required
def chat_list(request):
    if is_elderly(request.user):
        assignments = Assignment.objects.filter(elderly=request.user, active=True)
    elif is_caregiver(request.user):
        assignments = Assignment.objects.filter(caregiver=request.user, active=True)
    elif is_admin(request.user):
        assignments = Assignment.objects.all()
    else:
        assignments = []
    return render(request, 'eldercare_chat/chat_list.html', {'assignments': assignments})

@login_required
def chat_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    # Permission: only elderly, assigned caregiver, or admin
    if not (request.user == assignment.elderly or request.user == assignment.caregiver or is_admin(request.user)):
        messages.error(request, 'You do not have permission to view this chat.')
        return redirect('eldercare_chat:chat_list')
    
    chat, _ = Chat.objects.get_or_create(assignment=assignment)
    messages_qs = Message.objects.filter(chat=chat).order_by('timestamp')
    
    # Determine the other user in the conversation
    other_user = assignment.caregiver if request.user == assignment.elderly else assignment.elderly
    
    if request.method == 'POST' and (request.user == assignment.elderly or request.user == assignment.caregiver):
        content = request.POST.get('content')
        if content:
            send_message(chat, request.user, content)
            return redirect('eldercare_chat:chat_detail', assignment_id=assignment.id)
    
    return render(request, 'eldercare_chat/chat_detail.html', {
        'chat': chat,
        'assignment': assignment,
        'messages': messages_qs,
        'other_user': other_user
    })

@login_required
@user_passes_test(is_elderly)
def find_caregivers(request):
    """
    View for elderly users to find and connect with caregivers
    """
    # Get all available caregivers
    caregivers = User.objects.filter(role='caregiver', is_active=True)
    
    return render(request, 'eldercare_chat/find_caregivers.html', {
        'caregivers': caregivers
    })

@login_required
@user_passes_test(is_elderly)
def request_caregiver(request, caregiver_id):
    """
    View for elderly users to request a connection with a caregiver
    """
    caregiver = get_object_or_404(User, id=caregiver_id, role='caregiver')
    elderly = request.user
    
    # Check if there's already an active assignment
    existing_assignment = Assignment.objects.filter(
        elderly=elderly,
        caregiver=caregiver,
        active=True
    ).first()
    
    if existing_assignment:
        messages.info(request, f'You are already connected with {caregiver.get_full_name()}.')
        return redirect('eldercare_chat:chat_detail', assignment_id=existing_assignment.id)
    
    # Create a new assignment
    assignment = assign_caregiver_to_elderly(elderly, caregiver)
    messages.success(request, f'Connection request sent to {caregiver.get_full_name()}.')
    
    # Create a chat for this assignment
    chat = create_chat(assignment)
    
    # Redirect to the chat
    return redirect('eldercare_chat:chat_detail', assignment_id=assignment.id)

@login_required
@user_passes_test(is_admin)
def assign_caregiver_view(request):
    elderly_users = User.objects.filter(role='elderly')
    caregivers = User.objects.filter(role='caregiver')
    if request.method == 'POST':
        elderly_id = request.POST.get('elderly_id')
        caregiver_id = request.POST.get('caregiver_id')
        elderly = get_object_or_404(User, id=elderly_id, role='elderly')
        caregiver = get_object_or_404(User, id=caregiver_id, role='caregiver')
        assign_caregiver_to_elderly(elderly, caregiver)
        messages.success(request, f'Caregiver {caregiver.username} assigned to {elderly.username}.')
        return redirect('eldercare_chat:chat_list')
    return render(request, 'eldercare_chat/assign_caregiver.html', {'elderly_users': elderly_users, 'caregivers': caregivers})

@login_required
@require_POST
def send_message_view(request, chat_id):
    """
    API endpoint for sending a message in a chat
    """
    # Get the chat and verify the user is part of it
    try:
        chat = Chat.objects.get(id=chat_id)
        assignment = chat.assignment
        
        # Check if user is part of this chat
        if request.user != assignment.elderly and request.user != assignment.caregiver:
            return JsonResponse({'error': "You don't have permission to send messages in this chat."}, status=403)
        
        # Get message content
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': "Message content cannot be empty."}, status=400)
        
        # Create the message
        message = send_message(chat, request.user, content)
        
        # Return success response
        return JsonResponse({
            'status': 'success',
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': message.sender.id
            }
        })
        
    except Chat.DoesNotExist:
        return JsonResponse({'error': "Chat not found."}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_new_messages(request, chat_id):
    """
    API endpoint to check for new messages since the last message ID
    """
    try:
        chat = Chat.objects.get(id=chat_id)
        assignment = chat.assignment
        
        # Check if user is part of this chat
        if request.user != assignment.elderly and request.user != assignment.caregiver:
            return JsonResponse({'error': "You don't have permission to access this chat."}, status=403)
        
        # Get the last message ID from the request
        last_id = request.GET.get('last_id')
        
        if not last_id:
            return JsonResponse({'messages': []})
        
        # Get new messages
        new_messages = Message.objects.filter(
            chat=chat,
            id__gt=last_id
        ).order_by('timestamp')
        
        # Format messages for JSON response
        messages_data = [{
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sender_id': message.sender.id
        } for message in new_messages]
        
        return JsonResponse({'messages': messages_data})
        
    except Chat.DoesNotExist:
        return JsonResponse({'error': "Chat not found."}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
