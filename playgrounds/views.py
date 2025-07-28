from datetime import datetime, timedelta, time as dt_time

from django.utils import timezone
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions, serializers
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
        user = self.request.user
        if user.is_authenticated and user.role == 'seller':
            return queryset.filter(company=user)
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

    @swagger_auto_schema(...)
    def create(self, request, *args, **kwargs):
        images = request.FILES.getlist('images', [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sport_venue = serializer.save()

        for image in images:
            SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(...)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        images = request.FILES.getlist('images', [])
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        sport_venue = serializer.save()

        for image in images:
            SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

        return Response(serializer.data)

    @swagger_auto_schema(...)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(...)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(...)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def check_availability(self, request, pk=None):
        sport_venue = self.get_object()
        date_str = request.query_params.get('date')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            now = timezone.now()
            if date < now.date():
                return Response({'error': 'Нельзя забронировать дату в прошлом'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Неверный формат даты. Используйте формат YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        start_day = timezone.make_aware(datetime.combine(date, dt_time(8, 0)))
        end_day = timezone.make_aware(datetime.combine(date, dt_time(22, 30)))

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
                local_time = timezone.localtime(current)
                booked.add(local_time.strftime('%H:%M'))
                current += timedelta(minutes=30)

        slots = []
        current = datetime.combine(date, dt_time(8, 0))
        end = datetime.combine(date, dt_time(22, 30))
        while current <= end:
            aware_time = timezone.make_aware(current)
            time_str = timezone.localtime(aware_time).strftime('%H:%M')
            is_available = aware_time > timezone.now() if date == timezone.now().date() else True
            slots.append({'time': time_str, 'is_available': is_available and time_str not in booked})
            current += timedelta(minutes=30)

        return Response({
            'date': date_str,
            'working_hours': {'start': '08:00', 'end': '22:30'},
            'time_points': slots
        })


class FavoriteSportVenueViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteSportVenue.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        sport_venue_id = self.request.data.get('sport_venue')
        if FavoriteSportVenue.objects.filter(user=self.request.user, sport_venue_id=sport_venue_id).exists():
            raise serializers.ValidationError("Эта площадка уже добавлена в избранное")
        serializer.save(user=self.request.user)

    @swagger_auto_schema(...)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(...)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(...)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class SportVenueTypeViewSet(viewsets.ModelViewSet):
    queryset = SportVenueType.objects.all()
    serializer_class = SportVenueTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(...)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(...)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]
