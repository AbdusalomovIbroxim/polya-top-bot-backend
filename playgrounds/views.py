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
    company = filters.NumberFilter(field_name="company__id")

    class Meta:
        model = SportVenue
        fields = ['min_price', 'max_price', 'company']


# @csrf_exempt_api
# class SportVenueViewSet(viewsets.ModelViewSet):
#     queryset = SportVenue.objects.select_related('sport_venue_type', 'region', 'company').prefetch_related('images').all()
#     serializer_class = SportVenueSerializer
#     filterset_class = SportVenueFilter
#     parser_classes = (MultiPartParser, FormParser)
#     permission_classes = [AllowAny]

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         user = self.request.user
#         if user.is_authenticated and user.role == Role.OWNER:
#             return queryset.filter(company=user)
#         return queryset

#     def perform_create(self, serializer):
#         if self.request.user.role != 'seller':
#             raise permissions.PermissionDenied("Only sellers can create playgrounds")
#         serializer.save(company=self.request.user)

#     def perform_update(self, serializer):
#         if self.request.user.role != 'seller' or serializer.instance.company != self.request.user:
#             raise permissions.PermissionDenied("Only the owner can update this playground")
#         serializer.save()

#     def perform_destroy(self, instance):
#         if self.request.user.role != 'seller' or instance.company != self.request.user:
#             raise permissions.PermissionDenied("Only the owner can delete this playground")
#         instance.delete()

#     @action(detail=True, methods=['post'])
#     def add_image(self, request, pk=None):
#         sport_venue = self.get_object()
#         if request.user.role != 'seller' or sport_venue.company != request.user:
#             raise permissions.PermissionDenied("Only the owner can add images")

#         serializer = SportVenueImageSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(sport_venue=sport_venue)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['delete'])
#     def remove_image(self, request, pk=None):
#         sport_venue = self.get_object()
#         if request.user.role != 'seller' or sport_venue.company != request.user:
#             raise permissions.PermissionDenied("Only the owner can remove images")

#         image_id = request.data.get('image_id')
#         try:
#             image = sport_venue.images.get(id=image_id)
#             image.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except SportVenueImage.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND)

#     @swagger_auto_schema(
#         operation_description="Создает новую спортивную площадку с возможностью загрузки нескольких изображений",
#         manual_parameters=[
#             openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Название площадки'),
#             openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Описание площадки'),
#             openapi.Parameter('price_per_hour', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description='Цена за час'),
#             openapi.Parameter('city', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Город'),
#             openapi.Parameter('address', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Адрес'),
#             openapi.Parameter('latitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER, required=False, description='Широта'),
#             openapi.Parameter('longitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER, required=False, description='Долгота'),
#             openapi.Parameter('yandex_map_url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='URL Яндекс карты'),
#             openapi.Parameter('sport_venue_type', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='Тип площадки'),
#             openapi.Parameter('region', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='Регион'),
#             openapi.Parameter('deposit_amount', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description='Сумма депозита'),
#             openapi.Parameter('company_id', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='ID компании'),
#             openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Изображения площадки')
#         ],
#         responses={
#             201: "Созданная спортивная площадка",
#             400: "Bad Request"
#         }
#     )
#     def create(self, request, *args, **kwargs):
#         images = request.FILES.getlist('images', [])
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         sport_venue = serializer.save()

#         for image in images:
#             SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     @swagger_auto_schema(
#         operation_description="Обновляет существующую спортивную площадку и позволяет добавить новые изображения",
#         manual_parameters=[
#             openapi.Parameter('name', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Название площадки'),
#             openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Описание площадки'),
#             openapi.Parameter('price_per_hour', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description='Цена за час'),
#             openapi.Parameter('city', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Город'),
#             openapi.Parameter('address', openapi.IN_FORM, type=openapi.TYPE_STRING, description='Адрес'),
#             openapi.Parameter('latitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER, required=False, description='Широта'),
#             openapi.Parameter('longitude', openapi.IN_FORM, type=openapi.TYPE_NUMBER, required=False, description='Долгота'),
#             openapi.Parameter('yandex_map_url', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='URL Яндекс карты'),
#             openapi.Parameter('sport_venue_type', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='Тип площадки'),
#             openapi.Parameter('region', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='Регион'),
#             openapi.Parameter('deposit_amount', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description='Сумма депозита'),
#             openapi.Parameter('company_id', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description='ID компании'),
#             openapi.Parameter('images', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Изображения площадки')
#         ],
#         responses={
#             200: "Обновленная спортивная площадка",
#             400: "Bad Request",
#             404: "Not Found"
#         }
#     )
#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         images = request.FILES.getlist('images', [])
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         sport_venue = serializer.save()

#         for image in images:
#             SportVenueImage.objects.create(sport_venue=sport_venue, image=image)

#         return Response(serializer.data)

#     @swagger_auto_schema(
#         operation_description="Возвращает список всех доступных игровых полей",
#         responses={
#             200: "Список спортивных площадок"
#         }
#     )
#     def list(self, request, *args, **kwargs):
#         return super().list(request, *args, **kwargs)

#     @swagger_auto_schema(
#         operation_description="Возвращает детальную информацию о конкретном игровом поле",
#         responses={
#             200: "Детальная информация о спортивной площадке",
#             404: "Not Found"
#         }
#     )
#     def retrieve(self, request, *args, **kwargs):
#         return super().retrieve(request, *args, **kwargs)

#     @swagger_auto_schema(
#         operation_description="Удаляет игровое поле и все связанные с ним изображения",
#         responses={
#             204: "No Content",
#             404: "Not Found"
#         }
#     )
#     def destroy(self, request, *args, **kwargs):
#         return super().destroy(request, *args, **kwargs)

#     @swagger_auto_schema(
#         operation_description="Проверить доступность площадки на определенную дату",
#         manual_parameters=[
#             openapi.Parameter('date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', 
#                              description='Дата в формате YYYY-MM-DD', required=True)
#         ],
#         responses={
#             200: "Информация о доступности",
#             400: "Неверный формат даты или дата в прошлом"
#         }
#     )
#     @action(detail=True, methods=['get'])
#     def check_availability(self, request, pk=None):
#         sport_venue = self.get_object()
#         date_str = request.query_params.get('date')

#         try:
#             date = datetime.strptime(date_str, '%Y-%m-%d').date()
#             now = timezone.now()
#             if date < now.date():
#                 return Response({'error': 'Нельзя забронировать дату в прошлом'}, status=status.HTTP_400_BAD_REQUEST)
#         except (ValueError, TypeError):
#             return Response({'error': 'Неверный формат даты. Используйте формат YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

#         # Импортируем Booking здесь, чтобы избежать циклических импортов
#         from bookings.models import Booking
        
#         start_day = timezone.make_aware(datetime.combine(date, dt_time(8, 0)))
#         end_day = timezone.make_aware(datetime.combine(date, dt_time(22, 0)))

#         bookings = Booking.objects.filter(
#             sport_venue=sport_venue,
#             status__in=['PENDING', 'CONFIRMED'],
#             start_time__lt=end_day,
#             end_time__gt=start_day
#         )

#         booked = set()
#         for booking in bookings:
#             start = max(booking.start_time, start_day)
#             end = min(booking.end_time, end_day)
#             current = start
#             while current < end:
#                 local_time = timezone.localtime(current)
#                 booked.add(local_time.strftime('%H:%M'))
#                 current += timedelta(hours=1)

#         slots = []
#         current = datetime.combine(date, dt_time(8, 0))
#         end = datetime.combine(date, dt_time(22, 0))  # Изменили на 22:00
#         while current <= end:
#             aware_time = timezone.make_aware(current)
#             time_str = timezone.localtime(aware_time).strftime('%H:%M')
#             is_available = aware_time > timezone.now() if date == timezone.now().date() else True
#             slots.append({'time': time_str, 'is_available': is_available and time_str not in booked})
#             current += timedelta(hours=1)

#         return Response({
#             'date': date_str,
#             'working_hours': {'start': '08:00', 'end': '22:00'},
#             'time_points': slots
#         })

@csrf_exempt_api
class ClientSportVenueViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Для клиентов: список, детали и проверка свободного времени"""
    queryset = SportVenue.objects.select_related(
        'sport_venue_type', 'region', 'company'
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