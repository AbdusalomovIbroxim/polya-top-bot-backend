#!/usr/bin/env python
"""
Скрипт для автоматического обновления статуса истекших броней.
Можно запускать через cron или планировщик задач.
"""

import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from bookings.models import Booking
from django.utils import timezone

def update_expired_bookings():
    """
    Обновляет статус всех истекших броней
    """
    try:
        updated_count = Booking.update_expired_bookings()
        print(f"[{timezone.now()}] Обновлено {updated_count} истекших броней")
        return updated_count
    except Exception as e:
        print(f"[{timezone.now()}] Ошибка при обновлении броней: {e}")
        return 0

if __name__ == '__main__':
    update_expired_bookings() 