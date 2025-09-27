import os
import logging
from decimal import Decimal

import requests
from django.db import transaction
from django.utils import timezone
from playgrounds.models import SportVenue

from django.core.exceptions import ValidationError

from .models import Booking, Transaction

logger = logging.getLogger(__name__)



class SlotAlreadyBooked(Exception):
    """Слот уже занят другим пользователем."""
    pass


def create_booking(user, stadium: SportVenue, start_time, end_time, payment_method: str) -> Booking:
    """
    Создаёт бронь и транзакцию в статусе pending.
    Бросает исключения, если время некорректно или слот занят.
    """
    if start_time >= end_time:
        raise ValidationError({"detail": "Некорректное время бронирования"})

    # Проверка на пересечение броней
    overlap_exists = Booking.objects.filter(
        stadium=stadium,
        status=Booking.STATUS_PENDING,  # учитываем только активные брони
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()
    if overlap_exists:
        raise SlotAlreadyBooked("Слот уже занят")

    duration_hours = Decimal((end_time - start_time).total_seconds()) / Decimal(3600)
    amount = duration_hours * stadium.price_per_hour

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                stadium=stadium,
                start_time=start_time,
                end_time=end_time,
                amount=amount,
                payment_method=payment_method,
            )
            Transaction.objects.create(
                booking=booking,
                user=user,
                provider="click" if payment_method == Booking.PAYMENT_CARD else "cash",
                amount=amount,
                status="pending",
            )
        return booking
    except Exception as exc:
        raise ValidationError({"detail": f"Ошибка при создании брони: {exc}"})



def send_telegram_invoice(booking: Booking) -> dict:
    """
    Отправляет Telegram Invoice пользователю (если метод оплаты = карта).
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
    if not bot_token or not provider_token:
        raise RuntimeError("Telegram tokens not configured")

    if not getattr(booking.user, "telegram_id", None):
        raise RuntimeError("User has no telegram_id")

    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"

    payload_str = f"booking_{booking.id}_{int(timezone.now().timestamp())}"
    prices = [{
        "label": f"Бронирование {booking.stadium.name}",
        "amount": int(booking.amount * Decimal(100))
    }]

    body = {
        "chat_id": booking.user.telegram_id,
        "title": f"Оплата брони #{booking.id}",
        "description": f"Оплата бронирования стадиона {booking.stadium.name}",
        "payload": payload_str,
        "provider_token": provider_token,
        "currency": "UZS",
        "prices": prices,
        "start_parameter": "booking_payment",
    }

    resp = requests.post(url, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()


def handle_pre_checkout_query(pre_checkout_query: dict) -> dict:
    """
    Подтверждает pre_checkout_query у Telegram (answerPreCheckoutQuery).
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("Telegram bot token not configured")
        raise RuntimeError("Telegram bot token not configured")

    url = f"https://api.telegram.org/bot{bot_token}/answerPreCheckoutQuery"
    payload = {"pre_checkout_query_id": pre_checkout_query.get("id"), "ok": True}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        logger.info("Answered pre_checkout_query %s", pre_checkout_query.get("id"))
        return {"ok": True}
    except Exception:
        logger.exception("Failed to answer pre_checkout_query")
        return {"ok": False}


@transaction.atomic
def handle_successful_payment(invoice_payload: str, provider_info: dict) -> dict:
    """
    Обработка успешной оплаты (через Telegram или другого провайдера).
    Находим Transaction по payload → отмечаем как success → подтверждаем бронь.
    """
    try:
        tx = Transaction.objects.select_for_update().get(booking__transactions__provider="click", booking__transactions__status="pending")
    except Transaction.DoesNotExist:
        logger.error("Transaction with payload=%s not found", invoice_payload)
        return {"ok": False, "reason": "transaction_not_found"}

    tx.status = "success"
    tx.provider = "click"
    tx.save(update_fields=["status", "provider"])

    booking = tx.booking
    booking.status = Booking.STATUS_CONFIRMED
    booking.save(update_fields=["status"])

    logger.info("Payment confirmed for booking %s via transaction %s", booking.id, tx.id)
    return {"ok": True, "transaction_id": tx.id, "booking_id": booking.id}
