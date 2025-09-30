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
    serializer_class = BookingSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or self.request.user.is_anonymous:
            return Booking.objects.none()
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")

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
            logger.error("Ошибка при создании брони: %s", exc)
            raise ValidationError({"detail": "Внутренняя ошибка сервера при создании брони"})

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
                    properties={"detail": openapi.Schema(type=openapi.TYPE_STRING)},
                    example={"detail": "Бронь отменена"}
                )
            ),
            400: "Некорректные данные",
            403: "Чужая бронь",
            404: "Бронь не найдена",
        },
        operation_summary="Отмена брони пользователем",
        operation_description="Позволяет пользователю отменить свою бронь. В теле запроса нужно передать ID брони."
    )
    @action(detail=False, methods=["post"], url_path="cancel")
    def cancel(self, request):
        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response({"detail": "Не указан booking_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Бронь не найдена"}, status=status.HTTP_404_NOT_FOUND)

        if booking.user != request.user:
            return Response({"detail": "Вы не можете отменить чужую бронь"}, status=status.HTTP_403_FORBIDDEN)

        if booking.status != Booking.STATUS_PENDING:
            return Response({"detail": "Бронь нельзя отменить"}, status=status.HTTP_400_BAD_REQUEST)

        booking.cancel_booking()
        return Response({"detail": "Бронь отменена"}, status=status.HTTP_200_OK)


    @action(detail=False, methods=["post"], url_path="confirm_payment")
    def confirm_payment(self, request):
        payload = request.data.get("payload")
        external_id = request.data.get("telegram_charge_id")

        if not payload or not external_id:
            return Response({"detail": "Отсутствуют обязательные поля"}, status=status.HTTP_400_BAD_REQUEST)

        result = services.handle_successful_payment(payload, external_id)
        if not result["ok"]:
            return Response({"detail": result.get("reason", "Ошибка")}, status=status.HTTP_400_BAD_REQUEST)

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
