from django.shortcuts import render
from custom_admin.models import ContactMessage
from content.models import Article

def contact_view(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            success = True
    return render(request, 'contact.html', {'success': success})


def landing(request):
    articles = Article.objects.all().order_by('-published_at')[:3]
    return render(request, 'landing.html', {'articles': articles})
