from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import log_chatbot_interaction, get_openai_response
from accounts.models import User

@login_required
def chatbot_view(request):
    """Main chatbot interface view"""
    if not request.user.is_elderly():
        return render(request, 'chatbot/access_denied.html', {'error': 'Only Elderly users can access the chatbot.'}, status=403)
    
    return render(request, 'chatbot/chatbot.html')

@csrf_exempt
@login_required
def chatbot_api(request):
    if not request.user.is_elderly():
        return JsonResponse({'error': 'Only Elderly users can access the chatbot.'}, status=403)
    if request.method == 'POST':
        message = request.POST.get('message', '')
        # Use OpenAI API for response
        response = get_openai_response(message, request.user)
        log_chatbot_interaction(request.user, message, response)
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'POST required.'}, status=405)
