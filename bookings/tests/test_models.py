import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from stadiums.models import Stadium
from bookings.models import Booking, Transaction

# Получаем модель пользователя, чтобы она работала с любой кастомной моделью
User = get_user_model()


# Создаем фиктивные модели для тестирования
@pytest.fixture
def test_user(django_user_model):
    """Фикстура для создания тестового пользователя."""
    return django_user_model.objects.create(username="testuser", password="password")


@pytest.fixture
def test_stadium(db):
    """Фикстура для создания тестового стадиона."""
    return Stadium.objects.create(name="Test Stadium", price_per_hour=Decimal("50000.00"), capacity=11)


@pytest.mark.django_db
def test_booking_creation(test_user, test_stadium):
    """Проверка, что объект Booking создается корректно."""
    start_time = timezone.now() + timezone.timedelta(hours=1)
    end_time = start_time + timezone.timedelta(hours=2)
    booking = Booking.objects.create(
        user=test_user,
        stadium=test_stadium,
        start_time=start_time,
        end_time=end_time,
        amount=Decimal("100000.00"),
    )
    
    assert booking.user == test_user
    assert booking.stadium == test_stadium
    assert booking.amount == Decimal("100000.00")
    assert booking.status == Booking.STATUS_PENDING
    assert booking.payment_method is None
    assert isinstance(booking.created_at, timezone.datetime)


@pytest.mark.django_db
def test_booking_mark_expired_pending_status(test_user, test_stadium):
    """Проверка, что метод mark_expired правильно меняет статус на 'expired'."""
    # Создаем бронь, которая должна быть просрочена
    start_time = timezone.now() - timezone.timedelta(hours=2)
    end_time = timezone.now() - timezone.timedelta(hours=1)
    booking = Booking.objects.create(
        user=test_user,
        stadium=test_stadium,
        start_time=start_time,
        end_time=end_time,
        amount=Decimal("100.00"),
        status=Booking.STATUS_PENDING,
    )
    
    booking.mark_expired()
    booking.refresh_from_db()
    
    assert booking.status == Booking.STATUS_EXPIRED


@pytest.mark.django_db
def test_booking_mark_expired_confirmed_status(test_user, test_stadium):
    """Проверка, что метод mark_expired не меняет статус 'confirmed'."""
    # Создаем бронь, которая уже подтверждена, даже если время прошло
    start_time = timezone.now() - timezone.timedelta(hours=2)
    end_time = timezone.now() - timezone.timedelta(hours=1)
    booking = Booking.objects.create(
        user=test_user,
        stadium=test_stadium,
        start_time=start_time,
        end_time=end_time,
        amount=Decimal("100.00"),
        status=Booking.STATUS_CONFIRMED,
    )
    
    booking.mark_expired()
    booking.refresh_from_db()
    
    assert booking.status == Booking.STATUS_CONFIRMED


@pytest.mark.django_db
def test_transaction_creation(test_user, test_stadium):
    """Проверка, что объект Transaction создается корректно."""
    booking = Booking.objects.create(
        user=test_user,
        stadium=test_stadium,
        start_time=timezone.now(),
        end_time=timezone.now(),
        amount=Decimal("150.00"),
    )
    
    transaction = Transaction.objects.create(
        booking=booking,
        user=test_user,
        provider="cash",
        amount=booking.amount,
        status="success",
    )
    
    assert transaction.booking == booking
    assert transaction.user == test_user
    assert transaction.provider == "cash"
    assert transaction.amount == Decimal("150.00")
    assert transaction.status == "success"
    assert isinstance(transaction.created_at, timezone.datetime)
    assert isinstance(transaction.updated_at, timezone.datetime)
    assert transaction.created_at != transaction.updated_at # Проверяем, что updated_at обновился при создании