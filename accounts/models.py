from django.contrib.auth.models import AbstractUser
from django.db.models import TextChoices, CharField, Model, ForeignKey, CASCADE, DateTimeField, ImageField, BigIntegerField

class Role(TextChoices):
        SUPERADMIN = 'superadmin', 'Супер админ'        # Ты и другие владельцы проекта
        SUPPORT = 'support', 'Поддержка'                # Администраторы/саппорт
        OWNER = 'owner', 'Владелец поля'               # Владельцы спортивных полей (получают 10% с заказов)
        CUSTOMER = 'customer', 'Клиент'                # Пользователи, которые бронируют, ищут и смотрят поля

class User(AbstractUser):

    role = CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Роль'
    )
    
    photo = ImageField(upload_to='user/profile/avatar', verbose_name='Фотография', null=True)
    phone = CharField(max_length=15, blank=True, verbose_name='Телефон')
    telegram_id = BigIntegerField(null=True, blank=True, unique=True)
    # telegram_username = CharField(max_length=255, null=True, blank=True)
    # telegram_first_name = CharField(max_length=255, null=True, blank=True)
    # telegram_last_name = CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER

    @property
    def is_user(self):
        return self.role == self.Role.USER

