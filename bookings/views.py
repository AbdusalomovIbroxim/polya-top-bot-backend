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
                    description="ID брони для отмены"
                ),
            },
            required=["booking_id"],
            example={"booking_id": 123}
        ),
        responses={
            200: openapi.Response(
                description="Бронь успешно отменена",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    },
                    example={"detail": "Бронь отменена"}
                )
            ),
            400: openapi.Response(
                description="Некорректные данные или бронь нельзя отменить",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    },
                    example={"detail": "Бронь нельзя отменить"}
                )
            ),
            403: openapi.Response(
                description="Чужая бронь",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    },
                    example={"detail": "Вы не можете отменить чужую бронь"}
                )
            ),
            404: openapi.Response(
                description="Бронь не найдена",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    },
                    example={"detail": "Бронь не найдена"}
                )
            ),
        },
        operation_summary="Отмена брони пользователем",
        operation_description="Позволяет пользователю отменить свою бронь. В теле запроса нужно передать ID брони."
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
    
    @swagger_auto_schema(
        method="post",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "payload": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Payload, переданный в invoice"
                ),
                "amount": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Сумма платежа в копейках/тиынах"
                ),
                "telegram_charge_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="ID транзакции от Telegram"
                ),
            },
            required=["payload", "amount", "telegram_charge_id"],
            example={
                "payload": "booking_123",
                "amount": 100000,
                "telegram_charge_id": "abc123"
            }
        ),
        responses={
            200: openapi.Response(
                description="Оплата подтверждена",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
                    example={"detail": "Оплата подтверждена"}
                )
            ),
            400: "Некорректные данные",
            404: "Бронь не найдена",
        },
        operation_summary="Подтверждение оплаты от Telegram",
        operation_description="Вызывается ботом после успешной оплаты для подтверждения брони."
    )
    @action(detail=False, methods=["post"], url_path="confirm_payment")
    def confirm_payment(self, request):
        payload = request.data.get("payload")
        amount = request.data.get("amount")
        charge_id = request.data.get("telegram_charge_id")

        if not payload or not amount or not charge_id:
            return Response(
                {"detail": "Отсутствуют обязательные поля"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking_id = int(payload.split("_")[1])
            booking = Booking.objects.get(id=booking_id)
        except (ValueError, Booking.DoesNotExist):
            return Response(
                {"detail": "Бронь не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        if booking.status != Booking.STATUS_PENDING:
            return Response(
                {"detail": "Бронь уже обработана"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # фиксируем оплату
        booking.status = Booking.STATUS_CONFIRMED
        booking.payment_id = charge_id  # можно сохранить ID транзакции
        booking.save(update_fields=["status", "payment_id"])
        booking.transactions.update(status=Transaction.STATUS_PAID)


        return Response({"detail": "Оплата подтверждена"}, status=status.HTTP_200_OK)



class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()
        
        if self.request.user.is_anonymous:
            return Transaction.objects.none()
        
        return Transaction.objects.filter(user=self.request.user).order_by("-created_at")
