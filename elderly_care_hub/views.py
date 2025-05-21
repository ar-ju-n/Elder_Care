from django.shortcuts import render

from content.models import Article, HomepageSlide

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




def landing(request):
    articles = Article.objects.all().order_by('-published_at')[:3]
    slides = HomepageSlide.objects.all()
    return render(request, 'landing.html', {'articles': articles, 'slides': slides})

def about(request):
    return render(request, 'about.html')

def article_list(request):
    articles = Article.objects.all().order_by('-published_at')
    return render(request, 'content/article_list.html', {'articles': articles})

def video_list(request):
    videos = Video.objects.all().order_by('-published_at')
    return render(request, 'content/video_list.html', {'videos': videos})
