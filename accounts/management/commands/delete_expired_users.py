from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User

class Command(BaseCommand):
    help = 'Delete users whose scheduled_deletion_at has passed'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        users_to_delete = User.objects.filter(is_pending_deletion=True, scheduled_deletion_at__lte=now)
        count = users_to_delete.count()
        users_to_delete.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} users scheduled for deletion.")) 