from django.db import models
from django.utils.text import slugify
from unidecode import unidecode



class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название', null=True, blank=True, unique=True, default=None)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @classmethod
    def ensure_test_regions(cls):
        if not cls.objects.exists():
            test_data = [
                dict(name='Ташкент'),
                dict(name='Самарканд'),
                dict(name='Бухара'),
            ]
            for data in test_data:
                cls.objects.create(**data)

    def save(self, *args, **kwargs):
        if (not self.slug or self.slug.strip() == '') and self.name:
            base = slugify(unidecode(self.name))
            candidate = base or 'region'
            suffix = 1
            while Region.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                suffix += 1
                candidate = f"{base}-{suffix}"
            self.slug = candidate
        super().save(*args, **kwargs)


class SportVenueType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название типа')
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    is_indoor = models.BooleanField(default=False, verbose_name="Закрытое помещение")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тип площадки'
        verbose_name_plural = 'Типы площадок'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({'Закрытое' if self.is_indoor else 'Открытое'})"
    
    @classmethod
    def ensure_test_types(cls):
        if not cls.objects.exists():
            test_data = [
                dict(slug='football', name='Футбол'),
                dict(slug='basketball', name='Баскетбол'),
                dict(slug='tennis', name='Теннис'),
            ]
            for data in test_data:
                cls.objects.create(**data)



class SportVenue(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')

    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена за час')
    # deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Залоговая сумма', null=True, blank=True)

    city = models.CharField(max_length=100, verbose_name='Город', default='Ташкент')
    address = models.CharField(max_length=200, verbose_name='Адрес', default='Адрес не указан')

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        verbose_name='Регион',
        null=True,
        blank=True,
        related_name='sport_venues'
    )

    sport_venue_type = models.ForeignKey(
        SportVenueType,
        on_delete=models.SET_NULL,
        verbose_name='Тип площадки',
        null=True,
        blank=True,
        related_name='sport_venues'
    )

    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Владелец',
        related_name='sport_venues'
    )

    # Время работы
    open_time = models.TimeField(verbose_name="Время открытия", default="08:00")
    close_time = models.TimeField(verbose_name="Время закрытия", default="23:00")

    # Удобства
    has_lights = models.BooleanField(default=False, verbose_name="Освещение")
    has_lockers = models.BooleanField(default=False, verbose_name="Раздевалки")
    has_showers = models.BooleanField(default=False, verbose_name="Душевые")
    has_restrooms = models.BooleanField(default=False, verbose_name="Туалеты")
    has_walls = models.BooleanField(default=False, verbose_name="Ограждение/стены")
    has_parking = models.BooleanField(default=False, verbose_name="Парковка")

    # Гео
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Широта')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Долгота')
    yandex_map_url = models.URLField(max_length=500, null=True, blank=True, verbose_name='Ссылка на Яндекс Карты')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Спортивная площадка'
        verbose_name_plural = 'Спортивные площадки'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # if not self.deposit_amount:
        #     self.deposit_amount = self.price_per_hour
        super().save(*args, **kwargs)


class SportVenueImage(models.Model):
    sport_venue = models.ForeignKey(SportVenue, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='sport_venue_images/', verbose_name='Фотография')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Фотография площадки'
        verbose_name_plural = 'Фотографии площадок'

    def __str__(self):
        return f"Фото {self.sport_venue.name}"


class FavoriteSportVenue(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='favorite_sport_venues')
    sport_venue = models.ForeignKey(SportVenue, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'sport_venue')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.sport_venue.name}"
