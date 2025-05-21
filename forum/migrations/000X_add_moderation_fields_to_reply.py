from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('forum', '0001_initial'),  # Adjust as needed
    ]

    operations = [
        migrations.AddField(
            model_name='reply',
            name='is_approved',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='reply',
            name='is_flagged',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reply',
            name='moderation_notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
