from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PlaygroundType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название типа')
    description = models.TextField(verbose_name='Описание', blank=True)
    icon = models.ImageField(upload_to='playground_type_icons/', verbose_name='Иконка', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тип поля'
        verbose_name_plural = 'Типы полей'
        ordering = ['name']

    def __str__(self):
        return self.name

class Playground(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за час')
    city = models.CharField(max_length=100, verbose_name='Город', default='Ташкент')
    address = models.CharField(max_length=200, verbose_name='Адрес', default='Адрес не указан')
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Широта',
        help_text='Географическая широта',
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Долгота',
        help_text='Географическая долгота',
        null=True,
        blank=True
    )
    type = models.ForeignKey(
        PlaygroundType,
        on_delete=models.SET_NULL,
        verbose_name='Тип поля',
        null=True,
        blank=True,
        related_name='playgrounds'
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
