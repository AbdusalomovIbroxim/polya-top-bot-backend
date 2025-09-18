# from decimal import Decimal
# import logging

# from rest_framework import serializers
# from django.utils import timezone

# from .models import Event, EventParticipant, Payment, Booking
# from playgrounds.serializers import SportVenueSerializer
# from django.conf import settings

# logger = logging.getLogger(__name__)


# class EventParticipantSerializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(source="user.id", read_only=True)
#     username = serializers.CharField(source="user.username", read_only=True)
#     payment_method = serializers.ChoiceField(choices=EventParticipant.PAYMENT_METHOD_CHOICES, required=False)
#     payment_status = serializers.ChoiceField(choices=EventParticipant.PAYMENT_STATUS_CHOICES, read_only=True)

#     class Meta:
#         model = EventParticipant
#         fields = ("id", "user_id", "username", "payment_method", "payment_status", "joined_at")


# class PaymentSerializer(serializers.ModelSerializer):
#     event_participant = serializers.PrimaryKeyRelatedField(queryset=EventParticipant.objects.all())

#     class Meta:
#         model = Payment
#         fields = ("id", "event_participant", "amount", "status", "method", "provider_transaction_id", "payload", "created_at")
#         read_only_fields = ("id", "created_at")


# class EventReadSerializer(serializers.ModelSerializer):
#     field_details = SportVenueSerializer(source="field", read_only=True)
#     creator_id = serializers.IntegerField(source="creator.id", read_only=True)
#     participants = serializers.SerializerMethodField()
#     total_rent = serializers.SerializerMethodField()

#     class Meta:
#         model = Event
#         fields = ("id", "creator_id", "is_private", "field", "field_details",
#                   "game_time", "game_format", "rounds", "location", "participants", "total_rent", "created_at")
#         read_only_fields = ("id", "created_at", "location", "creator_id")

#     def get_participants(self, obj):
#         qs = obj.event_participants.select_related("user")
#         return EventParticipantSerializer(qs, many=True).data

#     def get_total_rent(self, obj):
#         return str(obj.get_total_rent())


# class CreateEventSerializer(serializers.ModelSerializer):
#     # При создании передаём id поля, game_time (1-5), game_format id (опционально), rounds и is_private
#     class Meta:
#         model = Event
#         fields = ("field", "game_time", "game_format", "rounds")
#         extra_kwargs = {
#             "rounds": {"required": True},
#             "game_time": {"required": True},
#             "field": {"required": True},
#         }

#     def validate_game_time(self, value):
#         if value < 1 or value > 7:
#             raise serializers.ValidationError("game_time должно быть от 1 до 5 часов")
#         return value

#     def validate_rounds(self, value):
#         if value < 1:
#             raise serializers.ValidationError("rounds должно быть >= 1")
#         return value

#     # def validate(self, data):
#         # """
#         # Проверяем профиль пользователя перед созданием: telegram_username и phone должны быть заполнены.
#         # Также убедимся, что поле существует.
#         # """
#         # user = self.context["request"].user
#         # Проверка профиля — ожидаем атрибуты telegram_username и phone на user
#         # if not getattr(user, "telegram_username", None) and not getattr(user, "telegram_id", None):
#         #     raise serializers.ValidationError("Заполните telegram username в профиле")
#         # if not getattr(user, "phone", None):
#         #     raise serializers.ValidationError("Заполните телефон в профиле")

#         # Доп. проверки по полю можно добавить при необходимости
#         return data

#     def create(self, validated_data):
#         request = self.context["request"]
#         user = request.user

#         # создаём Event и автоматически добавляем создателя как участника
#         event = Event.objects.create(creator=user, **validated_data)
#         # Добавляем создателя в EventParticipant
#         event.add_creator_as_participant()
#         logger.info("Event created %s by %s", event.id, user.username)
#         return event


# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields = ["id", "user", "field", "start_time", "end_time", "status", "created_at"]
#         read_only_fields = ["id", "status", "created_at", "user"]

#     def create(self, validated_data):
#         validated_data["user"] = self.context["request"].user
#         return super().create(validated_data)


from rest_framework import serializers
from .models import Booking, Transaction


class BookingSerializer(serializers.ModelSerializer):
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
        read_only_fields = ["status", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
