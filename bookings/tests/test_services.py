import os
import json
import pytest
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from bookings import services
from bookings.models import Booking, Transaction


@pytest.mark.django_db
def test_create_booking_creates_booking_and_transaction(user, stadium):
    start = timezone.now()
    end = start + timezone.timedelta(hours=2)
    booking = services.create_booking(
        user=user,
        stadium=stadium,
        start_time=start,
        end_time=end,
        amount=Decimal("120000.00"),
        payment_method=Booking.PAYMENT_CARD,
    )

    assert Booking.objects.filter(id=booking.id).exists()
    tx = Transaction.objects.filter(booking=booking).first()
    assert tx is not None
    assert tx.amount == Decimal("120000.00")
    assert tx.status == "pending"
    assert tx.provider == "click"


@pytest.mark.django_db
def test_send_telegram_invoice_success(monkeypatch, user, stadium):
    # Подготовим booking
    start = timezone.now()
    b = Booking.objects.create(user=user, stadium=stadium, start_time=start, end_time=start + timezone.timedelta(hours=1),
                               amount=Decimal("50000.00"), payment_method=Booking.PAYMENT_CARD)

    # Установим env
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("PAYMENT_PROVIDER_TOKEN", "provider-token")

    # Мокаем requests.post (Telegram API)
    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"ok": True, "result": {}}

    def fake_post(url, json=None, timeout=None):
        # проверим что тело содержит payload и chat_id
        assert "chat_id" in json
        assert "payload" in json
        return FakeResp()

    monkeypatch.setattr("bookings.services.requests.post", fake_post)

    res = services.send_telegram_invoice(b)
    assert res["ok"] is True
    assert "payload" in res
    # транзакция должна быть создана
    tx = Transaction.objects.filter(booking=b, provider="click", status="pending").last()
    assert tx is not None


@pytest.mark.django_db
def test_send_telegram_invoice_raises_when_no_env(monkeypatch, user, stadium):
    b = Booking.objects.create(user=user, stadium=stadium, start_time=timezone.now(),
                               end_time=timezone.now() + timezone.timedelta(hours=1),
                               amount=Decimal("40000.00"), payment_method=Booking.PAYMENT_CARD)
    # Очистим переменные
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("PAYMENT_PROVIDER_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        services.send_telegram_invoice(b)


@pytest.mark.django_db
def test_send_telegram_invoice_raises_when_user_no_chat(monkeypatch, user, stadium):
    # создаём пользователя без telegram_chat_id: сделаем временно None
    user_no_chat = user
    user_no_chat.telegram_chat_id = None
    user_no_chat.save(update_fields=["telegram_chat_id"])

    b = Booking.objects.create(user=user_no_chat, stadium=stadium, start_time=timezone.now(),
                               end_time=timezone.now() + timezone.timedelta(hours=1),
                               amount=Decimal("40000.00"), payment_method=Booking.PAYMENT_CARD)

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("PAYMENT_PROVIDER_TOKEN", "prov")
    with pytest.raises(RuntimeError):
        services.send_telegram_invoice(b)


@pytest.mark.django_db
def test_handle_pre_checkout_query_posts_answer(monkeypatch):
    # Подготовим fake response
    class FakeResp:
        def raise_for_status(self): pass

    called = {}

    def fake_post(url, json=None, timeout=None):
        # проверим что передаётся id и ok=True
        assert json.get("pre_checkout_query_id") is not None
        called["payload"] = json
        return FakeResp()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setattr("bookings.services.requests.post", fake_post)

    result = services.handle_pre_checkout_query({"id": "test_id"})
    assert result["ok"] is True
    assert called["payload"]["pre_checkout_query_id"] == "test_id"


@pytest.mark.django_db
def test_handle_pre_checkout_query_no_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        services.handle_pre_checkout_query({"id": "x"})


@pytest.mark.django_db
def test_handle_successful_payment_marks_transaction_and_booking(user, stadium):
    # Создаём booking и pending transaction
    b = Booking.objects.create(user=user, stadium=stadium, start_time=timezone.now(),
                               end_time=timezone.now() + timezone.timedelta(hours=1),
                               amount=Decimal("70000.00"), payment_method=Booking.PAYMENT_CARD)
    tx = Transaction.objects.create(booking=b, user=user, provider="click", amount=b.amount, status="pending")

    # В текущей реализации handle_successful_payment не смотрит в payload — он ищет pending transaction.
    res = services.handle_successful_payment("some_payload", {"provider_payment_charge_id": "tx-1"})
    assert res["ok"] is True
    tx.refresh_from_db()
    b.refresh_from_db()
    assert tx.status == "success"
    assert b.status == Booking.STATUS_CONFIRMED


@pytest.mark.django_db
def test_handle_successful_payment_no_pending_transaction_returns_error():
    # Нет транзакций
    res = services.handle_successful_payment("payload_missing", {"provider_payment_charge_id": "tx-1"})
    assert res["ok"] is False
    assert res["reason"] == "transaction_not_found"
