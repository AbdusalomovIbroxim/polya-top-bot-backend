from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class SportField(models.Model):
    SPORT_TYPES = [
        ('football', 'Футбольное поле'),
        ('basketball', 'Баскетбольная площадка'),
        ('volleyball', 'Волейбольная площадка'),
        ('tennis', 'Теннисный корт'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название поля')
    sport_type = models.CharField(max_length=20, choices=SPORT_TYPES, verbose_name='Тип спорта')
    description = models.TextField(verbose_name='Описание')
    address = models.CharField(max_length=500, verbose_name='Адрес')
    region = models.CharField(max_length=100, verbose_name='Регион')
    district = models.CharField(max_length=100, verbose_name='Район', blank=True, null=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за час')
    is_indoor = models.BooleanField(default=False, verbose_name='Крытое помещение')
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=0.0,
        verbose_name='Рейтинг'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Спортивное поле'
        verbose_name_plural = 'Спортивные поля'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_sport_type_display()})"
