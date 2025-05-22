"""
Event Management Views for Custom Admin
"""
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.utils import timezone

from events.models import Event
from events.forms import EventForm
from core.models import AuditLog

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def event_management(request):
    """
    Event management dashboard showing overview of events and registrations.
    """
    # Get upcoming and past events
    now = timezone.now()
    upcoming_events = Event.objects.filter(
        start_time__gte=now
    ).order_by('start_time')[:5]
    
    recent_events = Event.objects.filter(
        start_time__lt=now
    ).order_by('-start_time')[:5]
    
    # Get event statistics
    event_stats = {
        'total_events': Event.objects.count(),
        'upcoming_events': Event.objects.filter(start_time__gte=now).count(),
        'past_events': Event.objects.filter(start_time__lt=now).count(),
        'total_registrations': sum(event.attendees.count() for event in Event.objects.all()),
    }
    
    context = {
        'title': 'Event Management',
        'active_tab': 'events',
        'upcoming_events': upcoming_events,
        'recent_events': recent_events,
        'event_stats': event_stats,
    }
    
    return render(request, 'custom_admin/event_management.html', context)

@login_required
@user_passes_test(is_admin)
def event_list(request):
    """List all events"""
    events = Event.objects.all().order_by('-start_time')
    return render(request, 'custom_admin/events/event_list.html', {'events': events})

@login_required
@user_passes_test(is_admin)
def event_add(request):
    """Add a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event added successfully.')
            return redirect('custom_admin:event_list')
    else:
        form = EventForm()
    return render(request, 'custom_admin/events/event_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_admin)
def event_edit(request, event_id):
    """Edit an existing event"""
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully.')
            return redirect('custom_admin:event_list')
    else:
        form = EventForm(instance=event)
    return render(request, 'custom_admin/events/event_form.html', {'form': form, 'action': 'Edit'})

@login_required
@user_passes_test(is_admin)
def event_delete(request, event_id):
    """Delete an event"""
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('custom_admin:event_list')
    return render(request, 'custom_admin/confirm_delete.html', 
                 {'object': event, 'object_type': 'event'})

@login_required
@user_passes_test(is_admin)
def event_attendees(request, event_id):
    """View attendees for an event"""
    event = get_object_or_404(Event, id=event_id)
    attendees = event.attendees.all()
    return render(request, 'custom_admin/events/event_attendees.html', 
                 {'event': event, 'attendees': attendees})

@login_required
@user_passes_test(is_admin)
def export_events_csv(request):
    """Export events to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Start Time', 'End Time', 'Location', 'Attendees'])
    
    events = Event.objects.all().order_by('-start_time')
    for event in events:
        writer.writerow([
            event.title,
            event.start_time,
            event.end_time,
            event.location,
            event.attendees.count(),
        ])
    
    return response
