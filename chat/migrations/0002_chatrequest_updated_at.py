# Generated by Django 4.2.20 on 2025-05-22 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_remove_chatmessage_is_approved_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatrequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
