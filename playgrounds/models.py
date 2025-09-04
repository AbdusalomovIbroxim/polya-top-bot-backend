from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Role
from django.utils.text import slugify
from unidecode import unidecode

User = get_user_model()


class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')

    slug = models.SlugField(max_length=100, unique=True, verbose_name='Slug (для URL и фильтрации)', blank=True, null=True, help_text='Если оставить пустым, будет сгенерирован автоматически')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
        ordering = ['name']

    def __str__(self):
        return self.name

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


class SportVenueType(models.Model):
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Slug (URL-идентификатор)'
    )
    name = models.CharField(max_length=100, verbose_name='Название типа')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Тип площадки'
        verbose_name_plural = 'Типы площадок'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if (not self.slug or self.slug.strip() == '') and self.name:
            base = slugify(unidecode(self.name))
            candidate = base or 'type'
            suffix = 1
            while SportVenueType.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                suffix += 1
                candidate = f"{base}-{suffix}"
            self.slug = candidate
        super().save(*args, **kwargs)

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
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Залоговая сумма', null=True, blank=True)
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
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Владелец',
        related_name='sport_venues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Спортивная площадка'
        verbose_name_plural = 'Спортивные площадки'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.deposit_amount:
            self.deposit_amount = self.price_per_hour
        super().save(*args, **kwargs)

    @classmethod
    def ensure_test_venues(cls):
        if not cls.objects.exists():
            from django.contrib.auth import get_user_model
            from .models import SportVenueType, Region
            User = get_user_model()
            owner = User.objects.filter(role=Role.OWNER).first()
            venue_type = SportVenueType.objects.first()
            region = Region.objects.first()
            if not (owner and venue_type and region):
                return
            test_data = [
                dict(
                    name='Центральный стадион',
                    description='Главный стадион города',
                    price_per_hour=1000,
                    city='Ташкент',
                    address='ул. Центральная, 1',
                    latitude=41.2995,
                    longitude=69.2401,
                    sport_venue_type=venue_type,
                    region=region,
                    deposit_amount=500,
                    owner=owner
                ),
            ]
            for data in test_data:
                cls.objects.create(**data)


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
