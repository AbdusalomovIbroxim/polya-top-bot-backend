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
    provider = models.CharField(max_length=50)  # click, cash, payme, telegram
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
