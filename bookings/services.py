# import json
# import logging
# import os
# from decimal import Decimal

# import requests
# from django.db import transaction
# from django.utils import timezone
# from django.conf import settings

# from .models import Event, EventParticipant, Payment

# logger = logging.getLogger(__name__)


# def calculate_participant_amount(event: Event, capacity: int) -> Decimal:
#     """
#     Рассчитать сумму для одного участника:
#     total_rent = price_per_hour * game_time
#     amount_per_player = total_rent / capacity
#     """
#     total_rent = event.get_total_rent()
#     if capacity <= 0:
#         return Decimal("0.00")
#     amount = (total_rent / Decimal(capacity)).quantize(Decimal("0.01"))
#     logger.debug("Calculated participant amount %s for event %s (capacity=%s)", amount, event.id, capacity)
#     return amount


# def send_telegram_invoice_for_participant(event_participant: EventParticipant, amount: Decimal) -> dict:
#     """
#     Отправляет Telegram Invoice участнику. Возвращает dict с ответом API или ловит исключение.
#     Требует: TELEGRAM_BOT_TOKEN, PAYMENT_PROVIDER_TOKEN в окружении.
#     """
#     bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
#     provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
#     if not bot_token or not provider_token:
#         logger.error("Telegram or provider token not configured")
#         raise RuntimeError("Telegram or payment provider token not configured")

#     if not getattr(event_participant.user, "telegram_chat_id", None):
#         logger.error("User %s has no telegram_chat_id", event_participant.user)
#         raise RuntimeError("User has no telegram_chat_id")

#     url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"

#     payload_str = f"event_{event_participant.event.id}_user_{event_participant.user.id}_{int(timezone.now().timestamp())}"
#     # Сохраняем временно payload в Payment.payload if needed (create Payment record later)
#     prices = [{"label": f"Участие в событии {event_participant.event.id}", "amount": int(amount * Decimal(100))}]

#     body = {
#         "chat_id": event_participant.user.telegram_chat_id,
#         "title": f"Оплата участия в событии",
#         "description": f"Оплата участия в ивенте на поле {event_participant.event.field.name}",
#         "payload": payload_str,
#         "provider_token": provider_token,
#         "currency": "UZS" if os.getenv("CURRENCY", "UZS") == "UZS" else "RUB",
#         "prices": prices,
#         "start_parameter": "event_payment",
#     }

#     try:
#         resp = requests.post(url, json=body, timeout=10)
#         resp.raise_for_status()
#         data = resp.json()
#         logger.info("Telegram invoice sent %s for participant %s: %s", payload_str, event_participant.id, data.get("ok"))
#         # Create Payment record in pending state
#         payment = Payment.objects.create(
#             event_participant=event_participant,
#             amount=amount,
#             status=Payment.STATUS_PENDING,
#             method=Payment.METHOD_CLICK if getattr(event_participant, "payment_method", None) == EventParticipant.PAYMENT_METHOD_CLICK else Payment.METHOD_SYSTEM,
#             payload=payload_str,
#         )
#         return {"ok": True, "payload": payload_str, "payment_id": payment.id}
#     except Exception as exc:
#         logger.exception("Failed to send Telegram invoice: %s", exc)
#         raise


# def handle_pre_checkout_query(pre_checkout_query: dict) -> dict:
#     """
#     Подтверждает pre_checkout_query у Telegram (answerPreCheckoutQuery).
#     """
#     bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
#     if not bot_token:
#         logger.error("Telegram bot token not configured")
#         raise RuntimeError("Telegram bot token not configured")

#     url = f"https://api.telegram.org/bot{bot_token}/answerPreCheckoutQuery"
#     payload = {"pre_checkout_query_id": pre_checkout_query.get("id"), "ok": True}
#     try:
#         resp = requests.post(url, json=payload, timeout=5)
#         resp.raise_for_status()
#         logger.info("Answered pre_checkout_query %s", pre_checkout_query.get("id"))
#         return {"ok": True}
#     except Exception:
#         logger.exception("Failed to answer pre_checkout_query")
#         return {"ok": False}


# @transaction.atomic
# def handle_successful_payment(invoice_payload: str, provider_info: dict) -> dict:
#     """
#     Обработать успешную оплату от Telegram (или другого провайдера), найти Payment по payload,
#     перевести в статус PAID и отметить EventParticipant как оплаченного.
#     """
#     try:
#         payment = Payment.objects.select_for_update().get(payload=invoice_payload)
#     except Payment.DoesNotExist:
#         logger.error("Payment with payload=%s not found", invoice_payload)
#         return {"ok": False, "reason": "payment_not_found"}

#     payment.status = Payment.STATUS_CONFIRMED
#     payment.provider_transaction_id = provider_info.get("provider_payment_charge_id") or provider_info.get("provider_transaction_id")
#     payment.save(update_fields=["status", "provider_transaction_id"])

#     # отметить участника как оплаченного
#     ep = payment.event_participant
#     ep.payment_status = EventParticipant.PAYMENT_STATUS_PAID
#     ep.save(update_fields=["payment_status"])
#     logger.info("Payment %s confirmed and participant %s marked paid", payment.id, ep.id)
#     return {"ok": True, "payment_id": payment.id}



import os
import logging
from decimal import Decimal

import requests
from django.db import transaction
from django.utils import timezone

from .models import Booking, Transaction

logger = logging.getLogger(__name__)


def create_booking(user, stadium, start_time, end_time, amount: Decimal, payment_method: str) -> Booking:
    """
    Создаёт бронь и транзакцию в статусе pending.
    """
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


def send_telegram_invoice(booking: Booking) -> dict:
    """
    Отправляет Telegram Invoice пользователю (если метод оплаты = карта).
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
    if not bot_token or not provider_token:
        logger.error("Telegram or provider token not configured")
        raise RuntimeError("Telegram or provider token not configured")

    if not getattr(booking.user, "telegram_chat_id", None):
        logger.error("User %s has no telegram_chat_id", booking.user)
        raise RuntimeError("User has no telegram_chat_id")

    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"

    payload_str = f"booking_{booking.id}_{int(timezone.now().timestamp())}"
    prices = [{"label": f"Бронирование {booking.stadium.name}", "amount": int(booking.amount * Decimal(100))}]

    body = {
        "chat_id": booking.user.telegram_chat_id,
        "title": f"Оплата брони #{booking.id}",
        "description": f"Оплата бронирования стадиона {booking.stadium.name}",
        "payload": payload_str,
        "provider_token": provider_token,
        "currency": "UZS",
        "prices": prices,
        "start_parameter": "booking_payment",
    }

    try:
        resp = requests.post(url, json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Telegram invoice sent for booking %s: %s", booking.id, data.get("ok"))

        # Создаём транзакцию в pending
        tx = Transaction.objects.create(
            booking=booking,
            user=booking.user,
            provider="click",
            amount=booking.amount,
            status="pending",
        )
        # сохраняем payload, чтобы потом найти
        tx.provider = "click"
        tx.status = "pending"
        tx.save(update_fields=["provider", "status"])

        return {"ok": True, "payload": payload_str, "transaction_id": tx.id}
    except Exception as exc:
        logger.exception("Failed to send Telegram invoice: %s", exc)
        raise


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
