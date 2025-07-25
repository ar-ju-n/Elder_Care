# Generated by Django 5.2.1 on 2025-05-17 22:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('schedule', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('pay', models.DecimalField(decimal_places=2, max_digits=10)),
                ('approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_seen', models.BooleanField(default=False)),
                ('assigned_caregiver', models.ForeignKey(blank=True, limit_choices_to={'role': 'caregiver'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_jobs', to=settings.AUTH_USER_MODEL)),
                ('posted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posted_jobs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cover_letter', models.TextField(blank=True)),
                ('resume', models.FileField(blank=True, help_text='Upload your resume (PDF or Word document)', null=True, upload_to='resumes/')),
                ('credentials', models.FileField(blank=True, help_text='Upload your certifications or credentials (PDF format)', null=True, upload_to='credentials/')),
                ('reference_letter', models.FileField(blank=True, help_text='Upload reference letters if available', null=True, upload_to='references/')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('caregiver', models.ForeignKey(limit_choices_to={'role': 'caregiver'}, on_delete=django.db.models.deletion.CASCADE, related_name='applications', to=settings.AUTH_USER_MODEL)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobs.job')),
            ],
            options={
                'unique_together': {('job', 'caregiver')},
            },
        ),
    ]
