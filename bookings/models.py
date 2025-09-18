# import uuid
# from decimal import Decimal
# from django.db import models, transaction
# from django.utils import timezone
# from datetime import timedelta
# from decimal import Decimal
# from django.contrib.auth import get_user_model
# from accounts.models import FootballFormat
# from playgrounds.models import SportVenue  # adjust import if your model name differs

# User = get_user_model()


# class Event(models.Model):
#     """
#     Событие (ивент) — организованный матч/серия раундов на поле.
#     """
#     GAME_TIME_CHOICES = [
#         (1, "1 час"),
#         (2, "2 часа"),
#         (3, "3 часа"),
#         (4, "4 часа"),
#         (5, "5 часов"),
#     ]

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_events")
#     is_private = models.BooleanField(default=False, verbose_name="Приватный")
#     field = models.ForeignKey(
#         SportVenue, on_delete=models.CASCADE, related_name="events", verbose_name="Поле"
#     )
#     # future_time = timezone.now() + timedelta(days=5)
#     start_game_time = models.DateTimeField(verbose_name="Время начала игры", null=True, blank=True)
#     game_time = models.PositiveSmallIntegerField(choices=GAME_TIME_CHOICES, verbose_name="Время игры (часы)")
#     # game_format — связываем через строковую ссылку, чтобы избежать жёсткой зависимости
#     game_format = models.CharField(
#         max_length=5,
#         choices=FootballFormat.choices,
#         default=FootballFormat.FIVE,
#         verbose_name="Формат игры"
#     )
#     rounds = models.PositiveSmallIntegerField(default=1, verbose_name="Раундов")
#     # Локация всегда Ташкент, по умолчанию и не показываем на фронте
#     location = models.CharField(max_length=128, default="Ташкент", editable=False)
#     participants = models.ManyToManyField(User, through="EventParticipant", related_name="events")
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Событие"
#         verbose_name_plural = "События"
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"Event {self.id} by {self.creator} at {self.field.name} ({self.game_time}h)"

#     # ---- Helpers / Business logic ----
#     def get_total_rent(self) -> Decimal:
#         """
#         Общая стоимость аренды поля за весь период (price_per_hour * game_time).
#         """
#         if not self.field or self.field.price_per_hour is None:
#             return Decimal("0.00")
#         return (self.field.price_per_hour * Decimal(self.game_time)).quantize(Decimal("0.01"))

#     def get_participants_count(self) -> int:
#         return self.participants.count()

#     def get_free_slots(self, capacity: int) -> int:
#         """
#         Возвращает количество свободных слотов, если поле имеет capacity (максимум игроков).
#         capacity нужно получать от модели поля (например, field.capacity) — передаётся извне.
#         """
#         return max(0, capacity - self.get_participants_count())

#     def is_full(self, capacity: int) -> bool:
#         return self.get_participants_count() >= capacity

#     @transaction.atomic
#     def add_creator_as_participant(self, payment_method="system_money"):
#         """
#         Добавляет создателя в таблицу участников, если его там нет.
#         """
#         from django.db import IntegrityError

#         try:
#             EventParticipant.objects.create(
#                 event=self,
#                 user=self.creator,
#                 payment_method=payment_method,
#                 payment_status=EventParticipant.PAYMENT_STATUS_PENDING,
#             )
#         except IntegrityError:
#             # Уже есть — игнорируем
#             pass

#     def update_status_if_expired(self, end_time):
#         """
#         Если время события прошло (полный конец), можно ставить какой-то флаг/логирование.
#         Тут событие не хранит start_time/end_time — ожидалось, что Booking workflow
#         распределяет эти значения. Если понадобится, можно добавить start/end.
#         """
#         # Заглушка: ничего не делает сейчас.
#         return False



# class EventParticipant(models.Model):
#     """
#     Участник события — связывает Event и User, хранит способ оплаты и статус.
#     """
#     PAYMENT_METHOD_SYSTEM = "system_money"
#     PAYMENT_METHOD_CLICK = "click"
#     PAYMENT_METHOD_CASH = "cash"

#     PAYMENT_METHOD_CHOICES = [
#         (PAYMENT_METHOD_SYSTEM, "Система (баланс)"),
#         (PAYMENT_METHOD_CLICK, "Click"),
#         (PAYMENT_METHOD_CASH, "Наличные / Перевод"),
#     ]

#     PAYMENT_STATUS_PENDING = "pending"
#     PAYMENT_STATUS_PAID = "paid"
#     PAYMENT_STATUS_FAILED = "failed"

#     PAYMENT_STATUS_CHOICES = [
#         (PAYMENT_STATUS_PENDING, "Ожидает оплаты"),
#         (PAYMENT_STATUS_PAID, "Оплачено"),
#         (PAYMENT_STATUS_FAILED, "Ошибка оплаты"),
#     ]

#     event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="event_participants")
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_participations")
#     payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_SYSTEM)
#     payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
#     joined_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ("event", "user")
#         verbose_name = "Участник события"
#         verbose_name_plural = "Участники события"

#     def __str__(self):
#         return f"{self.user.username} in {self.event.id} ({self.payment_status})"



# class Payment(models.Model):
#     """
#     Отдельная модель платежа, привязанная к участнику события.
#     """
#     STATUS_PENDING = "pending"
#     STATUS_CONFIRMED = "confirmed"
#     STATUS_FAILED = "failed"

#     STATUS_CHOICES = [
#         (STATUS_PENDING, "Ожидание"),
#         (STATUS_CONFIRMED, "Подтвержено"),
#         (STATUS_FAILED, "Ошибка"),
#     ]

#     METHOD_SYSTEM = "system_money"
#     METHOD_CLICK = "click"
#     METHOD_CASH = "cash"

#     METHOD_CHOICES = [
#         (METHOD_SYSTEM, "Система баллов/денег"),
#         (METHOD_CLICK, "Click"),
#         (METHOD_CASH, "Наличные/Перевод"),
#     ]

#     event_participant = models.ForeignKey(EventParticipant, on_delete=models.CASCADE, related_name="payments")
#     amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
#     method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_SYSTEM)
#     provider_transaction_id = models.CharField(max_length=255, null=True, blank=True)
#     payload = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Платеж"
#         verbose_name_plural = "Платежи"
#         ordering = ["-created_at"]

#     def __str__(self):
#         return f"Payment {self.id} {self.method} {self.amount} ({self.status})"


# class Booking(models.Model):
#     STATUS_PENDING = "pending"
#     STATUS_CONFIRMED = "confirmed"
#     STATUS_CANCELLED = "cancelled"
#     STATUS_EXPIRED = "expired"

#     STATUS_CHOICES = [
#         (STATUS_PENDING, "В ожидании"),
#         (STATUS_CONFIRMED, "Подтверждено"),
#         (STATUS_CANCELLED, "Отменено"),
#         (STATUS_EXPIRED, "Просрочено"),
#     ]

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
#     field = models.ForeignKey(SportVenue, on_delete=models.CASCADE, related_name="bookings")
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         verbose_name = "Бронь"
#         verbose_name_plural = "Брони"
#         ordering = ["-created_at"]
#         unique_together = ("field", "start_time", "end_time")

#     def __str__(self):
#         return f"Booking {self.id} by {self.user} at {self.field}"

#     def mark_expired(self):
#         if self.end_time < timezone.now() and self.status not in [self.STATUS_CANCELLED, self.STATUS_EXPIRED]:
#             self.status = self.STATUS_EXPIRED
#             self.save()


from django.db import models
from django.conf import settings
from django.utils import timezone


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает оплаты"),
        (STATUS_CONFIRMED, "Подтверждена"),
        (STATUS_CANCELLED, "Отменена"),
        (STATUS_EXPIRED, "Просрочена"),
    ]

    PAYMENT_CARD = "card"
    PAYMENT_CASH = "cash"

    PAYMENT_CHOICES = [
        (PAYMENT_CARD, "Карта"),
        (PAYMENT_CASH, "Наличные"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stadium = models.ForeignKey("stadiums.Stadium", on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_expired(self):
        if self.status == self.STATUS_PENDING and self.end_time < timezone.now():
            self.status = self.STATUS_EXPIRED
            self.save()
        return self


class Transaction(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="transactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # click, cash
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")  # pending, success, failed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
