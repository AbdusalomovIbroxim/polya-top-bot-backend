# Generated by Django 5.2 on 2025-05-07 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playgrounds', '0002_alter_playground_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='playground',
            name='address',
            field=models.CharField(default='Адрес не указан', max_length=200, verbose_name='Адрес'),
        ),
        migrations.AddField(
            model_name='playground',
            name='city',
            field=models.CharField(default='Ташкент', max_length=100, verbose_name='Город'),
        ),
        migrations.AddField(
            model_name='playground',
            name='deposit_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Сумма депозита для бронирования', max_digits=10, verbose_name='Сумма депозита'),
        ),
        migrations.AddField(
            model_name='playground',
            name='type',
            field=models.CharField(choices=[('FOOTBALL', 'Футбол'), ('BASKETBALL', 'Баскетбол'), ('TENNIS', 'Теннис'), ('VOLLEYBALL', 'Волейбол'), ('OTHER', 'Другое')], default='FOOTBALL', max_length=20, verbose_name='Тип поля'),
        ),
    ]
