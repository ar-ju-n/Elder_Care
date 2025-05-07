from django.core.management.base import BaseCommand
from eldercare_chat.models import Skill

class Command(BaseCommand):
    help = 'Creates initial skills for caregivers'

    def handle(self, *args, **options):
        # List of common caregiver skills
        skills = [
            {"name": "Medication Management", "description": "Administering medications and ensuring proper dosage"},
            {"name": "Mobility Assistance", "description": "Helping with walking, transfers, and preventing falls"},
            {"name": "Meal Preparation", "description": "Preparing nutritious meals according to dietary needs"},
            {"name": "Personal Care", "description": "Assistance with bathing, grooming, and toileting"},
            {"name": "Companionship", "description": "Providing emotional support and engaging in activities"},
            {"name": "Dementia Care", "description": "Specialized care for individuals with dementia or Alzheimer's"},
            {"name": "First Aid", "description": "Basic first aid and emergency response"},
            {"name": "Housekeeping", "description": "Light cleaning and maintaining a safe environment"},
            {"name": "Transportation", "description": "Driving to appointments and errands"},
            {"name": "Exercise Assistance", "description": "Helping with prescribed exercises and physical activity"}
        ]
        
        # Create skills
        created_count = 0
        for skill_data in skills:
            skill, created = Skill.objects.get_or_create(
                name=skill_data["name"],
                defaults={"description": skill_data["description"]}
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} skills'))