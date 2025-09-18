# import json
# import logging


# from django.db import transaction
# from django.utils import timezone
# from django.http import JsonResponse
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django.shortcuts import get_object_or_404
# from rest_framework import viewsets, status, mixins
# from django_filters import rest_framework as filters
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from django.views.decorators.csrf import csrf_exempt, csrf_protect

# from .models import Event, EventParticipant, Payment, Booking
# from .serializers import (
#     EventReadSerializer, CreateEventSerializer,
#     EventParticipantSerializer, PaymentSerializer, BookingSerializer
# )

# logger = logging.getLogger(__name__)


# class EventFilter(filters.FilterSet):
#     field = filters.NumberFilter(field_name="field__id")
#     is_private = filters.BooleanFilter(field_name="is_private")

#     class Meta:
#         model = Event
#         fields = ["field", "is_private"]


# class EventViewSet(mixins.ListModelMixin,
#                    mixins.RetrieveModelMixin,
#                    viewsets.GenericViewSet,
#                    mixins.CreateModelMixin):
#     """
#     CRUD для Event'ов:
#     - list: публичные и приватные свои (creator == user)
#     - retrieve: если приватное — только участники/создатель
#     - create: проверка профиля, автоматическое добавление создателя в participants
#     """
#     queryset = Event.objects.all().select_related("creator", "field")
#     filterset_class = EventFilter

#     def get_permissions(self):
#         if self.action in ["list", "retrieve"]:
#             return [AllowAny()]
#         return [IsAuthenticated()]

#     def get_serializer_class(self):
#         if self.action in ["create"]:
#             return CreateEventSerializer
#         return EventReadSerializer

#     def list(self, request, *args, **kwargs):
#         user = request.user if request.user and request.user.is_authenticated else None
#         qs = self.get_queryset()
#         # Показываем все публичные + приватные, где пользователь участник или создатель
#         public_qs = qs.filter(is_private=False)
#         if user:
#             private_qs = qs.filter(is_private=True).filter(models.Q(creator=user) | models.Q(event_participants__user=user))
#             qs = (public_qs | private_qs).distinct()
#         else:
#             qs = public_qs
#         page = self.paginate_queryset(qs)
#         serializer = self.get_serializer(page, many=True)
#         return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

#     def retrieve(self, request, pk=None):
#         obj = get_object_or_404(self.get_queryset(), pk=pk)
#         # Если приватный — проверяем доступ
#         if obj.is_private:
#             user = request.user
#             if not user.is_authenticated:
#                 return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
#             is_participant = obj.event_participants.filter(user=user).exists()
#             if obj.creator != user and not is_participant:
#                 return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
#         serializer = EventReadSerializer(obj, context={"request": request})
#         return Response(serializer.data)

#     def perform_create(self, serializer):
#         # Создаём event через сериализатор (в нём добавится создатель как участник)
#         event = serializer.save()
#         logger.info("Event %s created", event.id)

#     @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
#     def join(self, request, pk=None):
#         """
#         Присоединиться к событию:
#         - проверяем, что событие публичное либо пользователь приглашён (опция)
#         - защищаем от гонок через select_for_update
#         - создаём EventParticipant
#         """
#         event = get_object_or_404(Event.objects.select_for_update(), pk=pk)
#         user = request.user

#         if event.is_private and event.creator != user:
#             # Дополнительно можно реализовать приглашения; пока запрещаем
#             return Response({"detail": "Приватное событие. Доступ закрыт."}, status=status.HTTP_403_FORBIDDEN)

#         # Получаем capacity поля, если есть attribute (например, field.capacity), иначе берём players_count default 10
#         capacity = getattr(event.field, "capacity", 10)

#         with transaction.atomic():
#             event_locked = Event.objects.select_for_update().get(pk=event.pk)
#             if event_locked.is_full(capacity):
#                 return Response({"detail": "Событие заполнено"}, status=status.HTTP_400_BAD_REQUEST)
#             # Создаём участника
#             try:
#                 ep = EventParticipant.objects.create(event=event_locked, user=user)
#             except Exception as exc:
#                 logger.exception("Failed to add participant: %s", exc)
#                 return Response({"detail": "Не удалось присоединиться (возможно уже участник)"}, status=status.HTTP_400_BAD_REQUEST)

#         serialized = EventParticipantSerializer(ep, context={"request": request})
#         return Response(serialized.data, status=status.HTTP_201_CREATED)

#     @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
#     def leave(self, request, pk=None):
#         event = get_object_or_404(Event, pk=pk)
#         user = request.user
#         try:
#             ep = EventParticipant.objects.get(event=event, user=user)
#             ep.delete()
#             return Response({"detail": "Вы вышли из события"}, status=status.HTTP_200_OK)
#         except EventParticipant.DoesNotExist:
#             return Response({"detail": "Вы не являетесь участником"}, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
#     def pay(self, request, pk=None):
#         """
#         Инициирует оплату для текущего пользователя (участника).
#         Ожидает тело: {"method": "system_money"|"click"|"cash"}
#         """
#         event = get_object_or_404(Event, pk=pk)
#         user = request.user
#         try:
#             ep = EventParticipant.objects.get(event=event, user=user)
#         except EventParticipant.DoesNotExist:
#             return Response({"detail": "Вы не участник события"}, status=status.HTTP_400_BAD_REQUEST)

#         method = request.data.get("method", EventParticipant.PAYMENT_METHOD_SYSTEM)
#         ep.payment_method = method
#         ep.save(update_fields=["payment_method"])

#         # Рассчитать сумму — для этого нужна capacity поля
#         capacity = getattr(event.field, "capacity", 10)
#         amount = services.calculate_participant_amount(event, capacity)

#         # Для offline cash — сразу создаём Payment и отмечаем paid=False (ожидается подтверждение вручную)
#         if method == EventParticipant.PAYMENT_METHOD_CASH:
#             p = Payment.objects.create(event_participant=ep, amount=amount, method=Payment.METHOD_CASH, status=Payment.STATUS_PENDING)
#             return Response({"detail": "Отметьте оплату при поступлении (наличные)", "payment_id": p.id}, status=status.HTTP_201_CREATED)

#         # Для click или system_money — делаем заглушку: если system_money, списываем внутренний баланс (если есть поле)
#         if method == EventParticipant.PAYMENT_METHOD_SYSTEM:
#             # Попытаться списать внутренний баланс пользователя (если есть поле balance)
#             balance = getattr(user, "balance", None)
#             if balance is None:
#                 return Response({"detail": "Внутренний баланс недоступен"}, status=status.HTTP_400_BAD_REQUEST)
#             if balance < amount:
#                 return Response({"detail": "Недостаточно средств на балансе"}, status=status.HTTP_400_BAD_REQUEST)
#             # Списываем (обновление баланса вынесите в реальную бизнес-логику)
#             user.balance = balance - amount
#             user.save(update_fields=["balance"])
#             p = Payment.objects.create(event_participant=ep, amount=amount, method=Payment.METHOD_SYSTEM, status=Payment.STATUS_CONFIRMED)
#             ep.payment_status = EventParticipant.PAYMENT_STATUS_PAID
#             ep.save(update_fields=["payment_status"])
#             return Response({"detail": "Оплата списана с баланса", "payment_id": p.id}, status=status.HTTP_200_OK)

#         # Для Click — можем отправить ссылку/инициировать платёж (заглушка: используем services to prepare invoice)
#         if method == EventParticipant.PAYMENT_METHOD_CLICK:
#             try:
#                 invoice = services.send_telegram_invoice_for_participant(ep, amount)
#                 return Response({"detail": "Invoice created", "payload": invoice.get("payload"), "payment_id": invoice.get("payment_id")}, status=status.HTTP_200_OK)
#             except Exception as exc:
#                 logger.exception("Click/Telegram invoice error: %s", exc)
#                 return Response({"detail": "Не удалось создать счёт"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# class BookingViewSet(viewsets.ModelViewSet):
#     serializer_class = BookingSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         # DRF гарантирует, что здесь user всегда аутентифицирован
#         return Booking.objects.filter(user=self.request.user).order_by("-created_at")

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         booking = self.get_object()
#         if booking.status not in [Booking.STATUS_CANCELLED, Booking.STATUS_EXPIRED]:
#             booking.status = Booking.STATUS_CANCELLED
#             booking.save()
#         return Response({"status": booking.status})

#     @action(detail=False, methods=["get"])
#     def expired(self, request):
#         qs = Booking.objects.filter(user=request.user, end_time__lt=timezone.now())
#         for b in qs:
#             b.mark_expired()
#         serializer = self.get_serializer(qs, many=True)
#         return Response(serializer.data)

#     @action(detail=False, methods=["get"])
#     def confirmed(self, request):
#         qs = Booking.objects.filter(user=request.user, status=Booking.STATUS_CONFIRMED)
#         serializer = self.get_serializer(qs, many=True)
#         return Response(serializer.data)

import json
import logging
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
import requests
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Booking, Transaction
from .serializers import BookingSerializer, TransactionSerializer
from . import services


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user, status=Booking.STATUS_PENDING)
        return booking

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        booking = self.get_object()
        payment_method = request.data.get("payment_method")

        if booking.status != Booking.STATUS_PENDING:
            return Response({"detail": "Бронь уже обработана"}, status=400)

        if payment_method not in [Booking.PAYMENT_CARD, Booking.PAYMENT_CASH]:
            return Response({"detail": "Некорректный метод оплаты"}, status=400)

        booking.payment_method = payment_method

        if payment_method == Booking.PAYMENT_CASH:
            booking.save()
            tx = Transaction.objects.create(
                booking=booking,
                user=request.user,
                provider="cash",
                amount=booking.amount,
                status="pending",
            )
            return Response({"detail": "Вы выбрали оплату наличными. Подтвердит администратор."})

        if payment_method == Booking.PAYMENT_CARD:
            # TODO: заменить на реальный API Click
            click_payload = {
                "service_id": "TEST",  # твой service_id
                "transaction_param": str(booking.id),
                "amount": str(booking.amount),
                "return_url": "https://your-domain.com/api/click/callback/",
            }
            # в реале -> запрос в Click API, а сейчас фейк URL
            payment_url = f"https://my.click.uz/pay/{booking.id}?amount={booking.amount}"

            booking.save()
            tx = Transaction.objects.create(
                booking=booking,
                user=request.user,
                provider="click",
                amount=booking.amount,
                status="pending",
            )
            return Response({"payment_url": payment_url})

    @action(detail=False, methods=["get"])
    def expired(self, request):
        qs = Booking.objects.filter(user=request.user, end_time__lt=timezone.now())
        for b in qs:
            b.mark_expired()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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


