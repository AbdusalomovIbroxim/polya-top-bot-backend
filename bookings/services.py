# services.py (пример)
import requests
import os
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from .models import Booking

def send_telegram_invoice(booking: Booking):
    """
    Отправляет счёт в Telegram на основе данных бронирования.
    """
    if not booking.user.telegram_chat_id:
        print(f"У пользователя {booking.user.username} нет Telegram Chat ID.")
        return False

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
    
    if not all([BOT_TOKEN, PAYMENT_PROVIDER_TOKEN]):
        print("Ошибка: токены не найдены.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice"
    
    # Создаем уникальный payload для этого бронирования
    payload_str = f"booking_{booking.pk}_{int(timezone.now().timestamp())}"
    booking.telegram_payload = payload_str
    booking.save(update_fields=['telegram_payload'])

    price_in_kopecks = int(booking.total_price * Decimal(100))
    duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600
    
    title = f"Аренда поля {booking.sport_venue.name}"
    description = f"Бронирование на {duration_hours:.2f} часа(ов) с {booking.start_time.strftime('%d.%m %H:%M')}"

    payload = {
        "chat_id": booking.user.telegram_chat_id,
        "title": title,
        "description": description,
        "payload": payload_str,
        "provider_token": PAYMENT_PROVIDER_TOKEN,
        "currency": "RUB",
        "prices": [
            {
                "label": title,
                "amount": price_in_kopecks
            }
        ],
        "start_parameter": "booking_payment"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        if data.get("ok"):
            print(f"Счёт успешно отправлен для бронирования {booking.pk}")
            return True
        else:
            print(f"Ошибка при отправке счёта: {data.get('description')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка: {e}")
        return False