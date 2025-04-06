from django.contrib.auth.models import AbstractUser
from django.db import models
from playground.models import SportField

ROLE_CHOICES = [
    ('user', 'User'),
    ('seller', 'Seller'),
    ('admin', 'Admin'),
    ('superadmin', 'Superadmin'),
]


class User(AbstractUser):
    first_name = models.CharField(max_length=30, verbose_name='Имя')
    last_name = models.CharField(max_length=30, verbose_name='Фамилия', blank=True)
    username = models.CharField(max_length=30, unique=True, verbose_name='Имя пользователя')
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    rating = models.FloatField(default=0.0, verbose_name='Рейтинг')
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name='Telegram ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name='Пользователь')
    field = models.ForeignKey(SportField, on_delete=models.CASCADE, related_name='bookings', verbose_name='Поле')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Общая стоимость')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-date', '-start_time']
        unique_together = ['field', 'date', 'start_time', 'end_time']

    def __str__(self):
        return f"Бронирование {self.field.name} пользователем {self.user.username} на {self.date}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            hours = (self.end_time.hour - self.start_time.hour)
            self.total_price = self.field.price_per_hour * hours
        super().save(*args, **kwargs)
