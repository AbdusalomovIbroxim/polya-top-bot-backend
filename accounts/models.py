from django.contrib.auth.models import AbstractUser
from django.db import models
from playgrounds.models import Region
from django.contrib.postgres.fields import ArrayField

# --- Choices (справочники) ---
class Role(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Супер админ'
    SUPPORT = 'support', 'Поддержка'
    OWNER = 'owner', 'Владелец поля'
    CUSTOMER = 'customer', 'Клиент'


class FootballExperience(models.TextChoices):
    NEWBIE = "newbie", "Менее года"
    AMATEUR = "amateur", "1-3 года"
    REGULAR = "regular", "3-5 лет"
    PRO = "pro", "Более 5 лет"


class FootballFrequency(models.TextChoices):
    NEVER = "never", "Вообще не играю"
    YEARLY = "yearly", "Несколько раз в год"
    MONTHLY = "monthly", "Несколько раз в месяц"
    WEEKLY = "weekly", "Несколько раз в неделю"


class FootballPosition(models.TextChoices):
    GK = "gk", "Вратарь"
    DEF = "def", "Защитник"
    MID = "mid", "Полузащитник"
    FWD = "fwd", "Нападающий"


class FootballFormat(models.TextChoices):
    THREE = "3x3", "3 на 3"
    FOUR = "4x4", "4 на 4"
    FIVE = "5x5", "5 на 5"
    SIX = "6x6", "6 на 6"
    SEVEN = "7x7", "7 на 7"
    EIGHT = "8x8", "8 на 8"
    NINE = "9x9", "9 на 9"
    TEN = "10x10", "10 на 10"
    ELEVEN = "11x11", "11 на 11"


# --- User model ---
class User(AbstractUser):
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Роль'
    )
    photo = models.ImageField(
        upload_to='user/profile/avatar',
        null=True,
        blank=True,
        verbose_name='Фотография'
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        # unique=True,
        verbose_name='Телефон'
    )
    language = models.CharField(
        max_length=10,
        default="ru",
        verbose_name="Язык"
    )
    
    city = models.ForeignKey("playgrounds.Region", verbose_name="Город", on_delete=models.CASCADE, null=True, blank=True)
    
    football_experience = models.CharField(
        max_length=20,
        choices=FootballExperience.choices,
        verbose_name="Опыт",
        null=True, blank=True,
        # default=FootballExperience.NEWBIE
    )
    football_frequency = models.CharField(
        max_length=20,
        choices=FootballFrequency.choices,
        verbose_name="Частота игры",
        null=True, blank=True,
        # default=FootballFrequency.NEVER    
    )
    
    football_competitions = models.BooleanField(
        default=False,
        verbose_name="Участвовали ли в соревнованиях?"
    )
    
    football_formats = ArrayField(
        models.CharField(max_length=10, choices=FootballFormat.choices),
        blank=True,
        null=True,
        default=list,
        verbose_name="Форматы игры"
    )
    
    football_position = models.CharField(
        max_length=10,
        choices=FootballPosition.choices,
        verbose_name="Позиция (вратарь, защитник и т.д.)",
        null=True, blank=True,
        # default=FootballPosition.MID
    )
    
    telegram_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram ID")

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
