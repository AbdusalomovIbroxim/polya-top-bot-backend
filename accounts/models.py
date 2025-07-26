from django.contrib.auth.models import AbstractUser
from django.db.models import TextChoices, CharField, BigIntegerField, Model, ForeignKey, CASCADE, DateTimeField, ImageField


class User(AbstractUser):
    class Role(TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        SELLER = 'SELLER', 'Продавец'
        USER = 'USER', 'Пользователь'

    role = CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль'
    )
    photo = ImageField(upload_to='user/profile/', verbose_name='Фотография', null=True)
    phone = CharField(max_length=15, blank=True, verbose_name='Телефон')
    # telegram_id = BigIntegerField(null=True, blank=True, unique=True)
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


class Company(Model):
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CompanyMember(Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('staff', 'Staff'),
    ]

    user = ForeignKey(User, on_delete=CASCADE)
    company = ForeignKey(Company, on_delete=CASCADE, related_name='members')
    role = CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user} - {self.company} ({self.role})"
