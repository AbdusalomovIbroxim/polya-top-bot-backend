from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from playgrounds.models import SportVenue
from decimal import Decimal

User = get_user_model()

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Ожидает подтверждения'),
        ('CONFIRMED', 'Подтверждено'),
        ('CANCELLED', 'Отменено'),
        ('COMPLETED', 'Завершено'),
        ('EXPIRED', 'Истекло'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Ожидает оплаты'),
        ('PAID', 'Оплачено'),
        ('REFUNDED', 'Возвращено'),
    ]

    sport_venue = models.ForeignKey(
        SportVenue,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Игровое поле',
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Пользователь',
        null=True,
        blank=True
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name='Ключ сессии'
    )
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Статус'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name='Статус оплаты'
    )
    payment_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Ссылка на оплату'
    )
    qr_code = models.ImageField(
        upload_to='qr_codes/',
        blank=True,
        null=True,
        verbose_name='QR-код'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость'
    )
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма депозита',
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'Бронирование {self.sport_venue.name} - {self.user.username} ({self.start_time.date()})'

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            # Вычисляем длительность в часах как Decimal
            duration = self.end_time - self.start_time
            duration_hours = Decimal(str(duration.total_seconds() / 3600))
            
            # Вычисляем общую стоимость
            self.total_price = self.sport_venue.price_per_hour * duration_hours
            
            # Устанавливаем сумму депозита
            self.deposit_amount = self.sport_venue.deposit_amount
        super().save(*args, **kwargs)

    def update_status_if_expired(self):
        """
        Автоматически обновляет статус брони, если время уже прошло
        """
        now = timezone.now()
        
        # Если время окончания уже прошло и статус не COMPLETED/CANCELLED/EXPIRED
        if (self.end_time < now and 
            self.status not in ['COMPLETED', 'CANCELLED', 'EXPIRED']):
            self.status = 'EXPIRED'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    @classmethod
    def update_expired_bookings(cls):
        """
        Обновляет статус всех истекших броней
        """
        now = timezone.now()
        expired_bookings = cls.objects.filter(
            end_time__lt=now,
            status__in=['PENDING', 'CONFIRMED']
        )
        
        updated_count = expired_bookings.update(
            status='EXPIRED',
            updated_at=now
        )
        
        return updated_count
