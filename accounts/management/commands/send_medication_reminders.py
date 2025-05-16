from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from accounts.models import MedicationReminder
from django.core.mail import send_mail
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send medication reminders via email.'

    def handle(self, *args, **options):
        now = timezone.localtime()
        minute_start = now.replace(second=0, microsecond=0)
        minute_end = minute_start + timedelta(minutes=1)
        reminders = MedicationReminder.objects.filter(
            active=True,
            notification_method='email',
            time_of_day__gte=minute_start.time(),
            time_of_day__lt=minute_end.time()
        )
        sent_count = 0
        for reminder in reminders:
            user = reminder.user
            subject = f"Medication Reminder: {reminder.medication_name}"
            message = f"Dear {user.username},\n\nThis is your reminder to take your medication:\n\n"
            message += f"Medication: {reminder.medication_name}\n"
            if reminder.dosage:
                message += f"Dosage: {reminder.dosage}\n"
            if reminder.notes:
                message += f"Notes: {reminder.notes}\n"
            message += f"Time: {reminder.time_of_day.strftime('%H:%M')}\n\nTake care!\n"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            sent_count += 1
        self.stdout.write(self.style.SUCCESS(f"Sent {sent_count} medication reminder(s) via email."))
