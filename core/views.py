from django.shortcuts import render
from django.views.generic import TemplateView

def test_view(request):
    return render(request, 'test.html')

class TestView(TemplateView):
    template_name = 'test.html'
