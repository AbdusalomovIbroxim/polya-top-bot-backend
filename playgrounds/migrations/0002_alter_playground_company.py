# Generated by Django 5.2 on 2025-05-07 10:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playgrounds', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='playground',
            name='company',
            field=models.ForeignKey(limit_choices_to={'role': 'SELLER'}, on_delete=django.db.models.deletion.CASCADE, related_name='playgrounds', to=settings.AUTH_USER_MODEL, verbose_name='Компания'),
        ),
    ]
