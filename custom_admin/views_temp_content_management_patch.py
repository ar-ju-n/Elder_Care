from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AdminArticleForm
from .models import Article

@login_required
@user_passes_test(lambda u: u.is_authenticated and (u.is_superuser or u.is_staff))
def content_management(request):
    article_form = AdminArticleForm()
    articles = Article.objects.all().order_by('-updated_at')
    context = {
        'article_form': article_form,
        'articles': articles,
    }
    return render(request, 'custom_admin/content_management.html', context)
