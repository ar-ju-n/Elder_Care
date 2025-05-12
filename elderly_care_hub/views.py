from django.shortcuts import render
from custom_admin.models import ContactMessage
from content.models import Article

def contact_view(request):
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, subject=subject or '', message=message)
            success = True
    return render(request, 'contact.html', {'success': success})


from custom_admin.models import DynamicPage, ContentBlock, ThemeSetting

def landing(request):
    articles = Article.objects.all().order_by('-published_at')[:3]
    return render(request, 'landing.html', {'articles': articles})

def about(request):
    return render(request, 'about.html')

def article_list(request):
    articles = Article.objects.all().order_by('-published_at')
    return render(request, 'content/article_list.html', {'articles': articles})

def video_list(request):
    videos = Video.objects.all().order_by('-published_at')
    return render(request, 'content/video_list.html', {'videos': videos})
