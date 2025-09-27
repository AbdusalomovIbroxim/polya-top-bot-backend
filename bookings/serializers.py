from rest_framework import serializers
from .models import Booking, Transaction
from playgrounds.models import SportVenue
import pytz
from django.utils import timezone
from datetime import datetime


class SportVenuePreviewSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = SportVenue
        fields = ["id", "name", "image", "sport_venue_type"]

    read_only_fields = ["id", "name", "image", "sport_venue_type"]
    
    def get_image(self, obj):
        first_image = obj.images.first()
        return first_image.image.url if first_image else None


class BookingSerializer(serializers.ModelSerializer):
    stadium = SportVenuePreviewSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "stadium",
            "start_time",
            "end_time",
            "amount",
            "status",
            "payment_method",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at", "amount"]


class BookingCreateSerializer(serializers.ModelSerializer):
    stadium = serializers.PrimaryKeyRelatedField(
        queryset=SportVenue.objects.all()
    )
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    tz = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Booking
        fields = [
            "stadium",
            "start_time",
            "end_time",
            "payment_method",
            "tz",
        ]
        
    def validate(self, data):
        stadium = data["stadium"]
        start_time = data["start_time"]
        end_time = data["end_time"]

        # Текущий момент (в Ташкенте)
        tz_tashkent = pytz.timezone("Asia/Tashkent")
        now_tashkent = timezone.now().astimezone(tz_tashkent)

        # Проверка: нельзя в прошлом
        if end_time <= now_tashkent:
            raise serializers.ValidationError("Нельзя бронировать прошедшее время.")

        # Проверка: end > start
        if end_time <= start_time:
            raise serializers.ValidationError("Время окончания должно быть позже начала.")

        # Проверка: длительность хотя бы 1 час
        if (end_time - start_time).total_seconds() < 3600:
            raise serializers.ValidationError("Минимальная длительность брони — 1 час.")

        # Рабочее время стадиона (Ташкент)
        start_day = tz_tashkent.localize(datetime.combine(start_time.date(), stadium.open_time))
        end_day = tz_tashkent.localize(datetime.combine(start_time.date(), stadium.close_time))

        # Проверка, что бронь внутри рабочего времени
        if start_time < start_day or end_time > end_day:
            raise serializers.ValidationError("Выбранное время вне рабочего графика площадки.")

        # Проверка пересечений с другими бронями
        conflicts = Booking.objects.filter(
            stadium=stadium,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
        )
        if conflicts.exists():
            raise serializers.ValidationError("Это время уже забронировано.")

        return data




class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

