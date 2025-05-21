from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Event

def event_list(request):
    events = Event.objects.order_by('start_time')
    return render(request, 'events/event_list.html', {'events': events})

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'events/event_detail.html', {'event': event})

@login_required
def event_rsvp(request, pk):
    event = get_object_or_404(Event, pk=pk)
    from accounts.models import Notification, User
    if request.method == 'POST':
        if request.user in event.attendees.all():
            event.attendees.remove(request.user)
        else:
            event.attendees.add(request.user)
            # Notify event creator if not self
            if event.created_by and event.created_by != request.user:
                Notification.objects.create(
                    user=event.created_by,
                    message=f"{request.user.get_full_name() or request.user.username} has RSVP'd to your event: {event.title}",
                    url=reverse('event_detail', args=[event.pk]),
                    notif_type='event_rsvp',
                )
    return HttpResponseRedirect(reverse('event_detail', args=[pk]))

# Stub for event creation notification
# To be called after an event is created (in your event creation view):
def notify_family_members_event_created(event):
    from accounts.models import Notification, User
    family_members = User.objects.filter(role=User.FAMILY)
    for user in family_members:
        Notification.objects.create(
            user=user,
            message=f"A new event has been created: {event.title}",
            url=reverse('event_detail', args=[event.pk]),
            notif_type='event_new',
        )

@login_required
def event_create(request):
    from accounts.models import User
    if request.user.is_caregiver() and not request.user.is_verified_caregiver():
        from django.contrib import messages
        messages.error(request, "Your caregiver account must be verified by an admin before you can create events.")
        return redirect('accounts:profile', user_id=request.user.id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        location = request.POST.get('location')
        if title and start_time and location:
            event = Event.objects.create(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                created_by=request.user
            )
            notify_family_members_event_created(event)
            return HttpResponseRedirect(reverse('event_detail', args=[event.pk]))
        else:
            return render(request, 'events/event_form.html', {'error': 'Please fill out all required fields.'})
    return render(request, 'events/event_form.html')

