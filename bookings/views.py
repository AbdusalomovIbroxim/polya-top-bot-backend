import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .services import send_telegram_invoice
from bookings.models import Booking
from accounts.models import Role
from bookings.serializers import BookingSerializer
from djangoProject.utils import csrf_exempt_api


class IsAuthenticatedOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class BookingFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="start_time", lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name="end_time", lookup_expr='lte')
    status = filters.CharFilter(field_name="status")
    sport_venue = filters.NumberFilter(field_name="sport_venue__id")
    user = filters.NumberFilter(field_name="user__id")

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'status', 'sport_venue', 'user']


@csrf_exempt_api
class BookingViewSet(mixins.ListModelMixin,       # GET /bookings/
    mixins.CreateModelMixin,     # POST /bookings/
    mixins.RetrieveModelMixin,   # GET /bookings/{id}/
    viewsets.GenericViewSet
    ):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    permission_classes = [IsAuthenticatedOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        Booking.update_expired_bookings()
    
        if not user.is_authenticated:
            return Booking.objects.none()

        return queryset.filter(user=user)

    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user)
        is_sent = send_telegram_invoice(booking)
        
        if not is_sent:
            print(f"Не удалось отправить счёт для бронирования {booking.id}. Проверьте логи.")


    @swagger_auto_schema(
        operation_description="Создает новое бронирование",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sport_venue': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID спортивной площадки'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время начала'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время окончания')
            },
            required=['sport_venue', 'start_time', 'end_time']
        ),
        responses={
            201: "Созданное бронирование",
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Список бронирований пользователя. Админы видят все бронирования, продавцы - бронирования своих площадок, обычные пользователи - только свои бронирования.",
        responses={
            200: "Список бронирований"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Детали одного бронирования",
        responses={
            200: "Детальная информация о бронировании",
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        booking = self.get_object()
        
        booking.update_status_if_expired()
        
        return super().retrieve(request, *args, **kwargs)




@csrf_exempt
def telegram_webhook(request):
    """
    Обрабатывает входящие вебхуки от Telegram.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Проверяем, является ли это уведомлением об успешной оплате
            if 'message' in data and 'successful_payment' in data['message']:
                payment_info = data['message']['successful_payment']
                payload = payment_info['invoice_payload']
                
                try:
                    # Находим бронирование по payload
                    booking = Booking.objects.get(telegram_payload=payload)
                    
                    # Обновляем статус бронирования
                    booking.payment_status = 'PAID'
                    booking.status = 'CONFIRMED'
                    booking.save(update_fields=['payment_status', 'status'])
                    
                    print(f"Оплата для бронирования {booking.pk} успешно принята.")
                    return JsonResponse({'status': 'ok'})
                    
                except Booking.DoesNotExist:
                    print(f"Бронирование с payload {payload} не найдено.")
                    return JsonResponse({'status': 'error', 'message': 'Booking not found'}, status=404)

            # TODO: Обработка pre_checkout_query
            # if 'pre_checkout_query' in data:
            #     # Отправьте ответ 'ok=True' для подтверждения платежа
            #     return JsonResponse({"ok": True})
            
            # Если это другой тип обновления, просто отвечаем 'ok'
            return JsonResponse({'status': 'ok'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)