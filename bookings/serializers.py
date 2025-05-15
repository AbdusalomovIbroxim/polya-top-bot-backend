from rest_framework import serializers
from .models import Booking
from playgrounds.serializers import PlaygroundSerializer
from accounts.serializers import UserSerializer
from django.utils import timezone
from datetime import timedelta

class BookingSerializer(serializers.ModelSerializer):
    playground_details = PlaygroundSerializer(source='playground', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'playground', 'playground_details', 'user', 'user_details',
            'start_time', 'end_time', 'status', 'payment_status', 'payment_url',
            'qr_code', 'total_price', 'deposit_amount', 'created_at', 'updated_at',
            'session_key'
        ]
        read_only_fields = [
            'total_price', 'deposit_amount', 'created_at', 'updated_at',
            'payment_status', 'payment_url', 'qr_code', 'session_key'
        ]

    def validate(self, data):
        # Проверяем, что время окончания больше времени начала
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("Время окончания должно быть позже времени начала")

        # Проверяем, что бронирование не в прошлом
        if data['start_time'] < timezone.now():
            raise serializers.ValidationError("Нельзя бронировать время в прошлом")

        # Проверяем, что длительность бронирования не превышает 24 часа
        duration = data['end_time'] - data['start_time']
        if duration > timedelta(hours=24):
            raise serializers.ValidationError("Максимальная длительность бронирования - 24 часа")

        # Проверяем, что время соответствует 30-минутным интервалам
        start_minutes = data['start_time'].minute
        end_minutes = data['end_time'].minute
        if start_minutes not in [0, 30] or end_minutes not in [0, 30]:
            raise serializers.ValidationError("Время должно быть кратно 30 минутам")

        # Проверяем, что время в пределах рабочего дня (8:00 - 22:30)
        start_hour = data['start_time'].hour
        end_hour = data['end_time'].hour
        if start_hour < 8 or (end_hour > 22 or (end_hour == 22 and end_minutes > 30)):
            raise serializers.ValidationError("Бронирование возможно только с 8:00 до 22:30")

        # Проверяем, нет ли пересечений с другими бронированиями
        overlapping_bookings = Booking.objects.filter(
            playground=data['playground'],
            status__in=['PENDING', 'CONFIRMED'],
            start_time__lt=data['end_time'],
            end_time__gt=data['start_time']
        )
        if overlapping_bookings.exists():
            raise serializers.ValidationError("Выбранное время уже забронировано")

        return data 