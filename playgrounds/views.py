from datetime import datetime, timedelta, time as dt_time

from django.utils import timezone
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from bookings.models import Booking
from .models import Playground, PlaygroundImage, FavoritePlayground, PlaygroundType
from .serializers import (
    PlaygroundSerializer,
    PlaygroundImageSerializer,
    FavoritePlaygroundSerializer,
    PlaygroundTypeSerializer
)
from djangoProject.utils import csrf_exempt_api


class PlaygroundFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price_per_hour", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price_per_hour", lookup_expr='lte')
    company = filters.NumberFilter(field_name="company__id")

    class Meta:
        model = Playground
        fields = ['min_price', 'max_price', 'company']


class PlaygroundViewSet(viewsets.ModelViewSet):
    queryset = Playground.objects.all()
    serializer_class = PlaygroundSerializer
    filterset_class = PlaygroundFilter
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
        playground = self.get_object()
        if request.user.role != 'seller' or playground.company != request.user:
            raise permissions.PermissionDenied("Only the owner can add images")

        serializer = PlaygroundImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(playground=playground)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_image(self, request, pk=None):
        playground = self.get_object()
        if request.user.role != 'seller' or playground.company != request.user:
            raise permissions.PermissionDenied("Only the owner can remove images")

        image_id = request.data.get('image_id')
        try:
            image = playground.images.get(id=image_id)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PlaygroundImage.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Создает новое игровое поле с возможностью загрузки нескольких изображений",
        request_body=PlaygroundSerializer,
        responses={
            201: PlaygroundSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        playground_data = request.data.copy()
        images = request.FILES.getlist('images', [])

        serializer = self.get_serializer(data=playground_data)
        serializer.is_valid(raise_exception=True)
        playground = serializer.save()

        # Сохраняем изображения
        for image in images:
            PlaygroundImage.objects.create(playground=playground, image=image)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Обновляет существующее игровое поле и позволяет добавить новые изображения",
        request_body=PlaygroundSerializer,
        responses={
            200: PlaygroundSerializer,
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        playground_data = request.data.copy()
        images = request.FILES.getlist('images', [])

        serializer = self.get_serializer(instance, data=playground_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        playground = serializer.save()

        # Добавляем новые изображения
        for image in images:
            PlaygroundImage.objects.create(playground=playground, image=image)

        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Возвращает список всех доступных игровых полей",
        responses={
            200: PlaygroundSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает детальную информацию о конкретном игровом поле",
        responses={
            200: PlaygroundSerializer,
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
        playground = self.get_object()
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
            playground=playground,
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


class FavoritePlaygroundViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritePlaygroundSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return FavoritePlayground.objects.none()
        return FavoritePlayground.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        playground_id = self.request.data.get('playground')
        if FavoritePlayground.objects.filter(user=self.request.user, playground_id=playground_id).exists():
            raise serializers.ValidationError("Это поле уже добавлено в избранное")
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Добавляет поле в избранное",
        responses={
            201: FavoritePlaygroundSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает список избранных полей пользователя",
        responses={
            200: FavoritePlaygroundSerializer(many=True)
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


class PlaygroundTypeViewSet(viewsets.ModelViewSet):
    queryset = PlaygroundType.objects.all()
    serializer_class = PlaygroundTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_description="Создает новый тип поля",
        responses={
            201: PlaygroundTypeSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает список всех типов полей",
        responses={
            200: PlaygroundTypeSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
