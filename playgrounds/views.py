from datetime import datetime, timedelta, time as dt_time

from django.utils import timezone
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions, serializers, mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet

from accounts.models import Role
from .models import SportVenue, SportVenueImage, FavoriteSportVenue, SportVenueType, Region
from .serializers import (
    SportVenueSerializer,
    SportVenueImageSerializer,
    FavoriteSportVenueSerializer,
    SportVenueTypeSerializer,
    RegionSerializer
)
from djangoProject.utils import csrf_exempt_api


class SportVenueFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price_per_hour", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price_per_hour", lookup_expr='lte')

    class Meta:
        model = SportVenue
        fields = ['min_price', 'max_price']


@csrf_exempt_api
class ClientSportVenueViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Для клиентов: список, детали и проверка свободного времени"""
    queryset = SportVenue.objects.select_related(
        'sport_venue_type', 'region',
    ).prefetch_related('images').all()
    serializer_class = SportVenueSerializer
    filterset_class = SportVenueFilter
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Список всех доступных спортивных площадок"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Детальная информация о площадке"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Проверить доступность площадки на определенную дату",
        manual_parameters=[
            openapi.Parameter(
                'date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date',
                description='Дата в формате YYYY-MM-DD', required=True
            )
        ]
    )
    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        sport_venue = self.get_object()
        date_str = request.query_params.get('date')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date < timezone.now().date():
                return Response({'error': 'Нельзя бронировать дату в прошлом'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Неверный формат даты. Используйте YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        from bookings.models import Booking
        start_day = timezone.make_aware(datetime.combine(date, dt_time(8, 0)))
        end_day = timezone.make_aware(datetime.combine(date, dt_time(22, 0)))

        bookings = Booking.objects.filter(
            sport_venue=sport_venue,
            status__in=['PENDING', 'CONFIRMED'],
            start_time__lt=end_day,
            end_time__gt=start_day
        )

        booked = set()
        for booking in bookings:
            start = max(booking.start_time, start_day)
            end = min(booking.end_time, end_day)
            current = start
            while current < end:
                booked.add(timezone.localtime(current).strftime('%H:%M'))
                current += timedelta(hours=1)

        slots = []
        current = datetime.combine(date, dt_time(8, 0))
        end = datetime.combine(date, dt_time(22, 0))
        while current <= end:
            aware_time = timezone.make_aware(current)
            time_str = timezone.localtime(aware_time).strftime('%H:%M')
            is_available = aware_time > timezone.now() if date == timezone.now().date() else True
            slots.append({'time': time_str, 'is_available': is_available and time_str not in booked})
            current += timedelta(hours=1)

        return Response({
            'date': date_str,
            'working_hours': {'start': '08:00', 'end': '22:00'},
            'time_points': slots
        })


@csrf_exempt_api
class FavoriteSportVenueViewSet(mixins.CreateModelMixin,     # POST /favorites/ (создание)
    mixins.ListModelMixin,       # GET /favorites/ (список)
    mixins.DestroyModelMixin,    # DELETE /favorites/{id}/ (удаление)
    viewsets.GenericViewSet):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FavoriteSportVenue.objects.all()
        user = self.request.user
        
        if not user.is_authenticated:
            return FavoriteSportVenue.objects.none()
        
        if getattr(user, 'role', None) == 'admin':
            print("admin")
            return queryset
        
        print("user")
        return FavoriteSportVenue.objects.filter(user=user)
    
    def perform_create(self, serializer):
        sport_venue_id = self.request.data.get('sport_venue')

        try:
            from .models import SportVenue
            SportVenue.objects.get(id=sport_venue_id)
        except SportVenue.DoesNotExist:
            raise serializers.ValidationError("Площадка с указанным ID не найдена")

        # Check if the sport venue is already in the user's favorites
        if FavoriteSportVenue.objects.filter(user=self.request.user, sport_venue_id=sport_venue_id).exists():
            raise serializers.ValidationError("Эта площадка уже добавлена в избранное")

        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Добавить площадку в избранное",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sport_venue': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID спортивной площадки')
            },
            required=['sport_venue']
        ),
        responses={
            201: "Площадка добавлена в избранное",
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить площадку из избранного",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Allow the user to remove a sport venue from their favorites.
        """
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Список избранных площадок пользователя",
        responses={200: "Список избранных площадок"}
    )
    def list(self, request, *args, **kwargs):
        """
        List all favorite sport venues for the authenticated user.
        """
        return super().list(request, *args, **kwargs)

class SportVenueTypeViewSet(ReadOnlyModelViewSet):
    queryset = SportVenueType.objects.all()
    serializer_class = SportVenueTypeSerializer
    permission_classes = [AllowAny]

class RegionViewSet(ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]