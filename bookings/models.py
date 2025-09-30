from django.db import models
from django.conf import settings
from django.utils import timezone
from playgrounds.models import SportVenue


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
    stadium = models.ForeignKey(SportVenue, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_expired(self):
        if self.status == self.STATUS_PENDING and self.end_time < timezone.now():
            self.status = self.STATUS_EXPIRED
            self.save(update_fields=["status"])
        return self

    def confirm_payment(self, external_id=None):
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status"])
        self.transactions.update(
            status=Transaction.STATUS_CONFIRMED,
            external_id=external_id
        )

    def cancel_booking(self):
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status"])
        self.transactions.update(status=Transaction.STATUS_CANCELLED)


class Transaction(models.Model):
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

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="transactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    external_id = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="ID транзакции у провайдера (click/payme/telegram/...)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def confirm(self, external_id=None):
        self.status = self.STATUS_CONFIRMED
        if external_id:
            self.external_id = external_id
        self.save(update_fields=["status", "external_id", "updated_at"])

    def cancel(self):
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status", "updated_at"])
