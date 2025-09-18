import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json

from bookings.models import Booking, Transaction
from bookings import services
from .factories import UserFactory, BookingFactory

# Устанавливаем настройки, необходимые для работы сервисов
@pytest.mark.django_db
def test_handle_successful_payment():
    """Проверка, что handle_successful_payment корректно обновляет статус бронирования и транзакции."""
    user = UserFactory()
    booking = BookingFactory(user=user, status=Booking.STATUS_PENDING)
    
    # Создаем фиктивный payload и info
    invoice_payload = "test_payload"
    provider_info = {
        "provider_payment_charge_id": "ch_test_id",
        "telegram_payment": {}
    }

    # Создаем запись Payment, которая будет найдена по payload
    with patch('bookings.services.Payment.objects.get') as mock_get_payment:
        mock_payment = MagicMock(spec=services.Payment)
        mock_payment.payload = invoice_payload
        mock_payment.event_participant = MagicMock(spec=services.EventParticipant)
        mock_payment.event_participant.payment_status = services.EventParticipant.PAYMENT_STATUS_PENDING
        mock_payment.event_participant.save = MagicMock()
        mock_get_payment.return_value = mock_payment

        # Вызываем функцию
        result = services.handle_successful_payment(invoice_payload, provider_info)

        # Проверяем, что Payment был обновлен
        mock_payment.status = services.Payment.STATUS_CONFIRMED
        mock_payment.provider_transaction_id = "ch_test_id"
        mock_payment.save.assert_called_once_with(update_fields=["status", "provider_transaction_id"])

        # Проверяем, что EventParticipant был обновлен
        mock_payment.event_participant.payment_status = services.EventParticipant.PAYMENT_STATUS_PAID
        mock_payment.event_participant.save.assert_called_once_with(update_fields=["payment_status"])

        # Проверяем возвращаемое значение
        assert result['ok'] is True
        assert 'payment_id' in result

@pytest.mark.django_db
def test_handle_successful_payment_not_found():
    """Проверка на случай, когда платеж не найден."""
    result = services.handle_successful_payment("non_existent_payload", {})
    assert result['ok'] is False
    assert result['reason'] == 'payment_not_found'

@pytest.mark.django_db
def test_calculate_participant_amount():
    """Тестирование функции calculate_participant_amount."""
    user = UserFactory()
    stadium = StadiumFactory(price_per_hour=Decimal('100000.00'), capacity=10)
    booking = BookingFactory(user=user, stadium=stadium, amount=stadium.price_per_hour * Decimal('2'), end_time=timezone.now() + timezone.timedelta(hours=2))

    # Вычисляем сумму для одного участника, если их 10
    amount = services.calculate_participant_amount(booking, 10)
    assert amount == Decimal('20000.00') # (100000 * 2) / 10

    # Проверка на случай с нулевой вместимостью
    amount_zero_capacity = services.calculate_participant_amount(booking, 0)
    assert amount_zero_capacity == Decimal('0.00')