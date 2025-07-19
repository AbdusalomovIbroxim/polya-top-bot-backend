from datetime import datetime, timedelta, time as dt_time

from django.utils import timezone
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from bookings.models import Booking
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
    company = filters.NumberFilter(field_name="company__id")

    class Meta:
        model = SportVenue
        fields = ['min_price', 'max_price', 'company']


class SportVenueViewSet(viewsets.ModelViewSet):
    queryset = SportVenue.objects.select_related('sport_venue_type', 'region', 'company').prefetch_related('images').all()
    serializer_class = SportVenueSerializer
    filterset_class = SportVenueFilter
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and self.request.user.role == 'seller':
            return queryset.filter(company=self.request.user)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role != 'seller':
            raise permissions.PermissionDenied("Only sellers can create playgrounds")
        serializer.save(company=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.role != 'seller' or serializer.instance.company != self.request.user:
            raise permissions.PermissionDenied("Only the owner can update this playground")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != 'seller' or instance.company != self.request.user:
            raise permissions.PermissionDenied("Only the owner can delete this playground")
        instance.delete()

    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        sport_venue = self.get_object()
        if request.user.role != 'seller' or sport_venue.company != request.user:
            raise permissions.PermissionDenied("Only the owner can add images")

        serializer = SportVenueImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sport_venue=sport_venue)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_image(self, request, pk=None):
        sport_venue = self.get_object()
        if request.user.role != 'seller' or sport_venue.company != request.user:
            raise permissions.PermissionDenied("Only the owner can remove images")

        image_id = request.data.get('image_id')
        try:
            image = sport_venue.images.get(id=image_id)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SportVenueImage.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Создает новую спортивную площадку с возможностью загрузки нескольких изображений",
        request_body=SportVenueSerializer,
        responses={
            201: SportVenueSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        sport_venue_data = request.data.copy()
        images = request.FILES.getlist('images', [])

        serializer = self.get_serializer(data=sport_venue_data)
        serializer.is_valid(raise_exception=True)
        sport_venue = serializer.save()

        # Сохраняем изображения
        for image in images:
            SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Обновляет существующую спортивную площадку и позволяет добавить новые изображения",
        request_body=SportVenueSerializer,
        responses={
            200: SportVenueSerializer,
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        sport_venue_data = request.data.copy()
        images = request.FILES.getlist('images', [])

        serializer = self.get_serializer(instance, data=sport_venue_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        sport_venue = serializer.save()

        # Добавляем новые изображения
        for image in images:
            SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Возвращает список всех доступных игровых полей",
        responses={
            200: SportVenueSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает детальную информацию о конкретном игровом поле",
        responses={
            200: SportVenueSerializer,
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удаляет игровое поле и все связанные с ним изображения",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        sport_venue = self.get_object()
        date_str = request.query_params.get('date')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            current_time = timezone.now()
            if date < current_time.date():
                return Response(
                    {'error': 'Нельзя забронировать дату в прошлом'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'Неверный формат даты. Используйте формат YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Время начала и конца дня в UTC
        start_of_day = timezone.make_aware(datetime.combine(date, dt_time(8, 0)))
        end_of_day = timezone.make_aware(datetime.combine(date, dt_time(22, 30)))

        # Найти бронирования, пересекающиеся с этим днём
        existing_bookings = Booking.objects.filter(
            sport_venue=sport_venue,
            status__in=['PENDING', 'CONFIRMED'],
            start_time__lt=end_of_day,
            end_time__gt=start_of_day
        )

        booked_slots = set()

        for booking in existing_bookings:
            # Берем максимум начала (между бронью и началом дня) и минимум конца (между бронью и концом дня)
            booking_start = max(booking.start_time, start_of_day)
            booking_end = min(booking.end_time, end_of_day)

            # Округляем до 30 минут
            current = booking_start
            while current < booking_end:
                # Конвертируем время в локальную временную зону
                local_time = timezone.localtime(current)
                booked_slots.add(local_time.strftime('%H:%M'))
                current += timedelta(minutes=30)

        # Рабочие часы
        working_hours = {
            'start': '08:00',
            'end': '22:30'
        }

        time_points = []
        current_slot = datetime.combine(date, dt_time(8, 0))
        end_slot = datetime.combine(date, dt_time(22, 30))

        while current_slot <= end_slot:
            slot_time = timezone.make_aware(current_slot)
            # Конвертируем время в локальную временную зону
            local_slot_time = timezone.localtime(slot_time)
            time_str = local_slot_time.strftime('%H:%M')

            is_available = True
            if date == current_time.date():
                is_available = slot_time > current_time
            if time_str in booked_slots:
                is_available = False

            time_points.append({
                'time': time_str,
                'is_available': is_available
            })

            current_slot += timedelta(minutes=30)

        return Response({
            'date': date_str,
            'working_hours': working_hours,
            'time_points': time_points
        })


class FavoriteSportVenueViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return FavoriteSportVenue.objects.none()
        return FavoriteSportVenue.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        sport_venue_id = self.request.data.get('sport_venue')
        if FavoriteSportVenue.objects.filter(user=self.request.user, sport_venue_id=sport_venue_id).exists():
            raise serializers.ValidationError("Эта площадка уже добавлена в избранное")
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Добавляет поле в избранное",
        responses={
            201: FavoriteSportVenueSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает список избранных полей пользователя",
        responses={
            200: FavoriteSportVenueSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удаляет поле из избранного",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class SportVenueTypeViewSet(viewsets.ModelViewSet):
    queryset = SportVenueType.objects.all()
    serializer_class = SportVenueTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_description="Создает новый тип поля",
        responses={
            201: SportVenueTypeSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает список всех типов полей",
        responses={
            200: SportVenueTypeSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]
