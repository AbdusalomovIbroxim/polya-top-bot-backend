from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Region(models.Model):
    name_ru = models.CharField(max_length=100, verbose_name='Название (русский)')
    name_uz = models.CharField(max_length=100, verbose_name='Название (узбекский)')
    name_en = models.CharField(max_length=100, verbose_name='Название (английский)')

    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug (для URL и фильтрации)')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
        ordering = ['name_ru']

    def __str__(self):
        return self.name_ru

    def get_name_by_lang(self, lang_code):
        if lang_code == 'uz':
            return self.name_uz
        elif lang_code == 'en':
            return self.name_en
        return self.name_ru



class SportVenueType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название типа')
    description = models.TextField(verbose_name='Описание', blank=True)
    icon = models.ImageField(upload_to='playground_type_icons/', verbose_name='Иконка', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тип площадки'
        verbose_name_plural = 'Типы площадок'
        ordering = ['name']

    def __str__(self):
        return self.name

class SportVenue(models.Model):
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
    yandex_map_url = models.URLField(
        max_length=500,
        verbose_name='Ссылка на Яндекс Карты',
        help_text='Ссылка на место в Яндекс Картах',
        null=True,
        blank=True
    )
    sport_venue_type = models.ForeignKey(
        SportVenueType,
        on_delete=models.SET_NULL,
        verbose_name='Тип площадки',
        null=True,
        blank=True,
        related_name='sport_venues'
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        verbose_name='Регион',
        null=True,
        blank=True,
        related_name='sport_venues'
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
        related_name='sport_venues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Спортивная площадка'
        verbose_name_plural = 'Спортивные площадки'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.deposit_amount:
            self.deposit_amount = self.price_per_hour
        super().save(*args, **kwargs)

class SportVenueImage(models.Model):
    sport_venue = models.ForeignKey(SportVenue, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='sport_venue_images/', verbose_name='Фотография')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Фотография площадки'
        verbose_name_plural = 'Фотографии площадок'

class FavoriteSportVenue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_sport_venues')
    sport_venue = models.ForeignKey(SportVenue, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sport_venue')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.sport_venue.name}"
