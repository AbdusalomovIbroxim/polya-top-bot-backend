import json
import logging
import requests
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.timezone import is_naive, get_current_timezone


from .serializers import BookingSerializer, TransactionSerializer, BookingCreateSerializer
from .models import Booking, Transaction
from . import services



logger = logging.getLogger(__name__)


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Вьюсет для работы с бронями:
    - список моих броней
    - создание брони
    - просмотр детали
    - отмена
    """
    serializer_class = BookingSerializer
    
    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        if self.request.user.is_anonymous:
            return Booking.objects.none()
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        payment_method = self.request.data.get("payment_method", Booking.PAYMENT_CASH)
        client_tz = self.request.data.get("tz")

        start_time = serializer.validated_data["start_time"]
        end_time = serializer.validated_data["end_time"]

        if client_tz:
            import pytz
            try:
                tz = pytz.timezone(client_tz)

                if is_naive(start_time):
                    start_time = tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(tz)

                if is_naive(end_time):
                    end_time = tz.localize(end_time)
                else:
                    end_time = end_time.astimezone(tz)

                # Переводим в текущую (серверную) таймзону
                start_time = start_time.astimezone(get_current_timezone())
                end_time = end_time.astimezone(get_current_timezone())

            except pytz.UnknownTimeZoneError:
                raise serializers.ValidationError({"tz": "Invalid timezone"})
            
        booking = services.create_booking(
            user=self.request.user,
            stadium=serializer.validated_data["stadium"],
            start_time=start_time,
            end_time=end_time,
            payment_method=payment_method,
        )

        if payment_method == Booking.PAYMENT_CARD:
            try:
                services.send_telegram_invoice(booking)
            except Exception as exc:
                logger = logging.getLogger(__name__)
                logger.error("Не удалось отправить invoice в Telegram: %s", exc)

        return booking


    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Отмена брони пользователем.
        """
        booking = self.get_object()
        if booking.status != Booking.STATUS_PENDING:
            return Response(
                {"detail": "Бронь нельзя отменить"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status"])
        return Response({"detail": "Бронь отменена"}, status=status.HTTP_200_OK)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        
        if self.request.user.is_anonymous:
            return Transaction.objects.none()
        
        return Transaction.objects.filter(user=self.request.user).order_by("-created_at")



@csrf_exempt
def telegram_webhook(request):
    """
    Обрабатывает Telegram webhook:
    - pre_checkout_query -> подтверждаем
    - successful_payment -> отмечаем платеж через services.handle_successful_payment
    """
    logger = logging.getLogger(__name__)
    if request.method != "POST":
        return JsonResponse({"ok": False, "reason": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        logger.exception("Invalid JSON in telegram webhook")
        return JsonResponse({"ok": False, "reason": "invalid_json"}, status=400)

    # pre_checkout_query
    if "pre_checkout_query" in data:
        result = services.handle_pre_checkout_query(data["pre_checkout_query"])
        return JsonResponse(result)

    # successful_payment
    if "message" in data and "successful_payment" in data["message"]:
        payment_info = data["message"]["successful_payment"]
        payload = payment_info.get("invoice_payload")
        provider_info = {
            "provider_payment_charge_id": payment_info.get("provider_payment_charge_id"),
            "telegram_payment": payment_info
        }
        result = services.handle_successful_payment(payload, provider_info)
        status_code = 200 if result.get("ok") else 404
        return JsonResponse(result, status=status_code)

    return JsonResponse({"ok": True})
