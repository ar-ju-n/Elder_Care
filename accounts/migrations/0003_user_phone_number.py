# Generated by Django 5.1.1 on 2025-05-20 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_caregiververification_certification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Phone number (e.g., +977 98XXXXXXXX)', max_length=20, null=True),
        ),
    ]
