import json
from django.http import JsonResponse
from django.shortcuts import render
import requests
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, mixins
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView

from djangoProject import settings
from bookings.models import Booking
from .models import SportVenue, SportVenueType, Region, FavoriteSportVenue
from .serializers import (
    SportVenueSerializer,
    SportVenueTypeSerializer,
    RegionSerializer,
    FavoriteSportVenueSerializer
)


import pytz


class SportVenueTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SportVenueType.objects.all()
    serializer_class = SportVenueTypeSerializer
    permission_classes = [permissions.AllowAny]

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]

class ClientSportVenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SportVenue.objects.all().prefetch_related('images', 'sport_venue_type', 'region')
    serializer_class = SportVenueSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sport_venue_type', 'region', 'city']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ["id", 'price_per_hour']

    @swagger_auto_schema(
        operation_description="Проверить доступность площадки на определённую дату",
        manual_parameters=[
            openapi.Parameter(
                'date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date',
                description='Дата в формате YYYY-MM-DD', required=True
            ),
            openapi.Parameter(
                'tz', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                description='Таймзона клиента (например, Europe/London)', required=True
            )
        ]
    )
    @action(detail=True, methods=['get'], url_path='available-time')
    def available_time(self, request, pk=None):
        sport_venue = self.get_object()
        date_str = request.query_params.get('date')
        tz_name = request.query_params.get('tz', 'UTC')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date < timezone.now().date():
                return Response({'error': 'Нельзя проверять дату в прошлом'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Неверный формат даты. Используйте YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            return Response({'error': f'Неверная таймзона: {tz_name}'}, status=status.HTTP_400_BAD_REQUEST)

        # Рабочее время в Ташкенте (основная зона)
        open_time = sport_venue.open_time
        close_time = sport_venue.close_time
        tz_tashkent = pytz.timezone("Asia/Tashkent")

        start_day = tz_tashkent.localize(datetime.combine(date, open_time))
        end_day = tz_tashkent.localize(datetime.combine(date, close_time))

        bookings = Booking.objects.filter(
            stadium=sport_venue,
            start_time__lt=end_day,
            end_time__gte=start_day,
            status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
        )

        # Все занятые часы (в UTC)
        booked = set()
        for booking in bookings:
            current = booking.start_time
            while current < booking.end_time:
                booked.add(current.astimezone(pytz.UTC).strftime('%H:%M'))
                current += timedelta(hours=1)

        # Формируем слоты
        slots = []
        current = start_day
        while current < end_day:
            # Слот в UTC
            slot_utc = current.astimezone(pytz.UTC)
            slot_str_utc = slot_utc.strftime('%H:%M')

            # Переводим слот в таймзону клиента
            slot_client = slot_utc.astimezone(user_tz)
            slot_str_client = slot_client.strftime('%H:%M')

            is_available = slot_str_utc not in booked

            slots.append({
                'time': slot_str_client,
                'is_available': is_available
            })
            current += timedelta(hours=1)

        return Response({
            'date': date_str,
            'working_hours': {
                'start': open_time.strftime('%H:%M'),
                'end': close_time.strftime('%H:%M'),
            },
            'time_points': slots
        })
        
        
class FavoriteSportVenueViewSet(
    mixins.ListModelMixin,       # GET /favorites/
    mixins.CreateModelMixin,     # POST /favorites/
    mixins.DestroyModelMixin,    # DELETE /favorites/{id}/
    viewsets.GenericViewSet
):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return FavoriteSportVenue.objects.none()
        return FavoriteSportVenue.objects.filter(user=self.request.user).select_related("sport_venue")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



def welcome(request):
    return render(request, "index.html")

def custom_page_not_found_view(request, exception):
    return render(request, "404.html", status=404)


class ContactFormAPIView(APIView):
    """
    Принимает POST-запрос с контактными данными и отправляет их в Telegram.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({"ok": False, "error": "Неверный формат JSON"}, status=status.HTTP_400_BAD_REQUEST)

        name = data.get("name", "Не указано")
        phone = data.get("phone", "Не указан")
        telegram_user = data.get("telegram", "Не указан")
        message = data.get("message", "Нет сообщения")

        text = f"""
📩 Новая заявка с сайта Polyatop:
👤 Имя: {name}
📞 Телефон: {phone}
💬 Telegram: {telegram_user}
📝 Сообщение: {message}"""

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}

        try:
            r = requests.post(url, json=payload, timeout=5)
            r.raise_for_status() # Вызывает ошибку для плохих HTTP-статусов
            return Response({"ok": True}, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)