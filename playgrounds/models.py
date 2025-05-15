from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Playground(models.Model):
    TYPE_CHOICES = [
        ('FOOTBALL', 'Футбол'),
        ('BASKETBALL', 'Баскетбол'),
        ('TENNIS', 'Теннис'),
        ('VOLLEYBALL', 'Волейбол'),
        ('OTHER', 'Другое'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за час')
    city = models.CharField(max_length=100, verbose_name='Город', default='Ташкент')
    address = models.CharField(max_length=200, verbose_name='Адрес', default='Адрес не указан')
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='FOOTBALL',
        verbose_name='Тип поля'
    )
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма депозита',
        help_text='Сумма депозита для бронирования',
        default=0
    )
    company = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Компания',
        limit_choices_to={'role': 'SELLER'},
        related_name='playgrounds'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Игровое поле'
        verbose_name_plural = 'Игровые поля'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Если депозит не указан, устанавливаем его равным цене за час
        if not self.deposit_amount:
            self.deposit_amount = self.price_per_hour
        super().save(*args, **kwargs)


class PlaygroundImage(models.Model):
    playground = models.ForeignKey(Playground, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='playground_images/', verbose_name='Фотография')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Фотография поля'
        verbose_name_plural = 'Фотографии полей'


class FavoritePlayground(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_playgrounds')
    playground = models.ForeignKey(Playground, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'playground')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.playground.name}"
