from django.core.management.base import BaseCommand
from accounts.models import User
from faker import Faker

class Command(BaseCommand):
    help = 'Add fake users for testing'

    def handle(self, *args, **kwargs):
        fake = Faker()
        for i in range(10):  # Add 10 fake users
            username = fake.user_name()
            email = fake.email()
            full_name = fake.name()
            address = fake.address().replace('\n', ', ')
            role = 'family' if i % 2 == 0 else 'caregiver'
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Testpass123!',
                full_name=full_name,
                address=address,
                role=role,
            )
            if role == 'caregiver':
                user.rate_per_hour = fake.random_int(min=500, max=2000)
                user.save()
            self.stdout.write(self.style.SUCCESS(f'Created {role}: {username}'))
