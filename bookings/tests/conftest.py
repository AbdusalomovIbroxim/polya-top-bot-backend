import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

# Подстрой под реальный модуль стадионов в проекте
from playgrounds.models import Stadium

User = get_user_model()


@pytest.fixture
def user(db):
    # Создаём пользователя с telegram_chat_id (используется в сервисах)
    return User.objects.create_user(username="testuser", password="pass123", telegram_chat_id=123456789)


@pytest.fixture
def stadium(db):
    # Простая модель стадиона (адаптируй поля под свою модель)
    return Stadium.objects.create(
        name="Test Stadium",
        price_per_hour=Decimal("100000.00"),
    )
