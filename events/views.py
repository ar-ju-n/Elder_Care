from django.shortcuts import render, get_object_or_404
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
    if request.method == 'POST':
        if request.user in event.attendees.all():
            event.attendees.remove(request.user)
        else:
            event.attendees.add(request.user)
    return HttpResponseRedirect(reverse('event_detail', args=[pk]))
