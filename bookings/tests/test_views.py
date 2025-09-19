import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse

from bookings.models import Booking, Transaction


@pytest.mark.django_db
def test_booking_create_authenticated(user, stadium):
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "stadium": stadium.id,
        "start_time": timezone.now().isoformat(),
        "end_time": (timezone.now() + timezone.timedelta(hours=1)).isoformat(),
        "amount": "75000.00",
        # не указываем payment_method на этапе создания — в твоём serializer он не required
    }

    resp = client.post("/api/bookings/", payload, format="json")
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == Booking.STATUS_PENDING
    assert data["amount"] == "75000.00"


@pytest.mark.django_db
def test_booking_pay_cash_creates_transaction(user, stadium):
    client = APIClient()
    client.force_authenticate(user=user)

    booking = Booking.objects.create(
        user=user,
        stadium=stadium,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        amount=Decimal("80000.00"),
    )

    resp = client.post(f"/api/bookings/{booking.id}/pay/", {"payment_method": Booking.PAYMENT_CASH}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert "Вы выбрали оплату наличными" in data["detail"]
    booking.refresh_from_db()
    assert booking.payment_method == Booking.PAYMENT_CASH
    assert Transaction.objects.filter(booking=booking, provider="cash").exists()


@pytest.mark.django_db
def test_booking_pay_card_returns_payment_url(user, stadium):
    client = APIClient()
    client.force_authenticate(user=user)

    booking = Booking.objects.create(
        user=user,
        stadium=stadium,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=1),
        amount=Decimal("90000.00"),
    )

    resp = client.post(f"/api/bookings/{booking.id}/pay/", {"payment_method": Booking.PAYMENT_CARD}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert "payment_url" in data
    booking.refresh_from_db()
    assert booking.payment_method == Booking.PAYMENT_CARD
    assert Transaction.objects.filter(booking=booking, provider="click").exists()


@pytest.mark.django_db
def test_expired_action_marks_booking_expired(user, stadium):
    client = APIClient()
    client.force_authenticate(user=user)

    booking = Booking.objects.create(
        user=user,
        stadium=stadium,
        start_time=timezone.now() - timezone.timedelta(hours=5),
        end_time=timezone.now() - timezone.timedelta(hours=4),
        amount=Decimal("60000.00"),
    )

    resp = client.get("/api/bookings/expired/")
    assert resp.status_code == 200
    booking.refresh_from_db()
    assert booking.status == Booking.STATUS_EXPIRED
