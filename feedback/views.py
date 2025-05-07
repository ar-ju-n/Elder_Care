from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Rating
from .services import submit_rating, hide_rating, respond_to_rating
from accounts.models import User
from django import forms

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['caregiver', 'stars', 'review_text', 'is_anonymous']

def feedback_list(request):
    ratings = Rating.objects.filter(is_hidden=False).order_by('-created_at')
    return render(request, 'feedback/feedback_list.html', {'ratings': ratings})

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            submit_rating(**form.cleaned_data, reviewer=request.user)
            messages.success(request, 'Feedback submitted.')
            return redirect('feedback:feedback_list')
    else:
        form = RatingForm()
    return render(request, 'feedback/submit_feedback.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_admin_role())
def moderate_feedback(request):
    ratings = Rating.objects.all().order_by('-created_at')
    if request.method == 'POST':
        rating_id = request.POST.get('rating_id')
        action = request.POST.get('action')
        rating = get_object_or_404(Rating, id=rating_id)
        if action == 'hide':
            hide_rating(rating)
            messages.success(request, 'Feedback hidden.')
        elif action == 'respond':
            response = request.POST.get('response')
            respond_to_rating(rating, response)
            messages.success(request, 'Response added.')
    return render(request, 'feedback/moderate_feedback.html', {'ratings': ratings})
