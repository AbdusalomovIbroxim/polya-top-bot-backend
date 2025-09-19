import json
import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking, Transaction
from bookings import services


@pytest.mark.django_db
def test_webhook_pre_checkout_query_calls_service(client, user, stadium, monkeypatch):
    # Создаём booking + transaction (необязательно)
    booking = Booking.objects.create(user=user, stadium=stadium, start_time=timezone.now(),
                                     end_time=timezone.now() + timezone.timedelta(hours=1),
                                     amount=Decimal("50000.00"), payment_method=Booking.PAYMENT_CARD)
    Transaction.objects.create(booking=booking, user=user, provider="click", amount=booking.amount, status="pending")

    called = {}

    def fake_handle_pre_checkout_query(data):
        called["data"] = data
        return {"ok": True}

    monkeypatch.setattr(services, "handle_pre_checkout_query", fake_handle_pre_checkout_query)

    payload = {
        "pre_checkout_query": {
            "id": "test_query",
            "from": {"id": user.telegram_chat_id},
            "currency": "UZS",
            "total_amount": int(booking.amount * Decimal(100)),
        }
    }

    resp = client.post(reverse("telegram_webhook"), data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "data" in called


@pytest.mark.django_db
def test_webhook_successful_payment_calls_service(client, user, stadium, monkeypatch):
    booking = Booking.objects.create(user=user, stadium=stadium, start_time=timezone.now(),
                                     end_time=timezone.now() + timezone.timedelta(hours=1),
                                     amount=Decimal("70000.00"), payment_method=Booking.PAYMENT_CARD)
    Transaction.objects.create(booking=booking, user=user, provider="click", amount=booking.amount, status="pending")

    called = {}

    def fake_handle_successful_payment(payload, provider_info):
        called["payload"] = payload
        called["provider_info"] = provider_info
        return {"ok": True}

    monkeypatch.setattr(services, "handle_successful_payment", fake_handle_successful_payment)

    payload = {
        "message": {
            "successful_payment": {
                "currency": "UZS",
                "total_amount": int(booking.amount * Decimal(100)),
                "invoice_payload": f"booking_{booking.id}",
                "provider_payment_charge_id": "tx-123",
            }
        }
    }

    resp = client.post(reverse("telegram_webhook"), data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "payload" in called
    assert called["payload"].startswith("booking_")
