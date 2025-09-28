import pytz
import json
import logging
import requests
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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


    @swagger_auto_schema(
        request_body=BookingCreateSerializer,
        responses={
            201: openapi.Response("Бронь успешно создана", BookingSerializer),
            400: "Некорректные данные (например: время некорректное)",
            409: "Слот уже занят другим пользователем",
            500: "Внутренняя ошибка сервера при создании брони",
        },
        operation_summary="Создание брони",
        operation_description="Создаёт новую бронь на указанный слот",
    )
    def create(self, request, *args, **kwargs):
        """Создание брони"""
        return super().create(request, *args, **kwargs)
    
    
    def perform_create(self, serializer):
        payment_method = self.request.data.get("payment_method", Booking.PAYMENT_CASH)

        start_time = serializer.validated_data["start_time"]
        end_time = serializer.validated_data["end_time"]

        try:
            booking = services.create_booking(
                user=self.request.user,
                stadium=serializer.validated_data["stadium"],
                start_time=start_time,
                end_time=end_time,
                payment_method=payment_method,
            )
        except services.SlotAlreadyBooked:
            raise ValidationError({"detail": "Слот уже занят"})
        except ValidationError as ve:
            raise ve
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error("Ошибка при создании брони: %s", exc)
            raise ValidationError({"detail": "Внутренняя ошибка сервера при создании брони"})

        if payment_method == Booking.PAYMENT_CARD:
            try:
                services.send_telegram_invoice(booking)
            except Exception as exc:
                logger = logging.getLogger(__name__)
                logger.error("Не удалось отправить invoice в Telegram: %s", exc)

        return booking

    @swagger_auto_schema(
        method="post",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "booking_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID брони, которую нужно отменить"
                ),
            },
            required=["booking_id"],
            example={"booking_id": 123}
        ),
        responses={
            200: openapi.Response(
                description="Бронь успешно отменена",
                examples={
                    "application/json": {"detail": "Бронь отменена"}
                }
            ),
            400: openapi.Response(
                description="Некорректные данные или бронь нельзя отменить",
                examples={
                    "application/json": {"detail": "Бронь нельзя отменить"}
                }
            ),
            403: openapi.Response(
                description="Пользователь пытается отменить чужую бронь",
                examples={
                    "application/json": {"detail": "Вы не можете отменить чужую бронь"}
                }
            ),
            404: openapi.Response(
                description="Бронь не найдена",
                examples={
                    "application/json": {"detail": "Бронь не найдена"}
                }
            ),
        },
        operation_summary="Отмена брони пользователем",
        operation_description=(
            "Позволяет пользователю отменить свою бронь.\n\n"
            "📌 В теле запроса нужно передать ID брони:\n\n"
            "```json\n"
            "{ \"booking_id\": 123 }\n"
            "```"
        )
    )
    @action(detail=False, methods=["post"], url_path="cancel")
    def cancel(self, request):
        """
        Отмена брони пользователем.
        Ожидает в теле JSON:
        {
            "booking_id": <id>
        }
        """
        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response(
                {"detail": "Не указан booking_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Бронь не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, что бронь принадлежит текущему пользователю
        if booking.user != request.user:
            return Response(
                {"detail": "Вы не можете отменить чужую бронь"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Проверяем статус
        if booking.status != Booking.STATUS_PENDING:
            return Response(
                {"detail": "Бронь нельзя отменить"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Отменяем
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
