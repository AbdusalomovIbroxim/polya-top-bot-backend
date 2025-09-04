from rest_framework import status, mixins, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from bookings.models import Booking
from bookings.serializers import BookingSerializer
from playgrounds.models import SportVenue, SportVenueImage
from playgrounds.serializers import SportVenueReadSerializer, SportVenueWriteSerializer
from accounts.models import Role
from djangoProject.utils import csrf_exempt_api
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg import openapi


@csrf_exempt_api
class OwnerSportVenueViewSet(viewsets.ModelViewSet):
    queryset = SportVenue.objects.select_related(
        'sport_venue_type', 'region', 'owner'
    ).prefetch_related('images').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SportVenueReadSerializer
        return SportVenueWriteSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == Role.OWNER:
            return SportVenue.objects.filter(owner=user)
        return SportVenue.objects.none()

    @swagger_auto_schema(
        operation_description="Создать площадку",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'description', 'price_per_hour', 'city', 'address'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, example='Центральный стадион'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, example='Главный стадион города с профессиональным покрытием'),
                'price_per_hour': openapi.Schema(type=openapi.TYPE_NUMBER, format='decimal', example=1000.00),
                'deposit_amount': openapi.Schema(type=openapi.TYPE_NUMBER, format='decimal', example=500.00),
                'city': openapi.Schema(type=openapi.TYPE_STRING, example='Ташкент'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, example='ул. Центральная, 1'),
                'latitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', example=41.2995),
                'longitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', example=69.2401),
                'yandex_map_url': openapi.Schema(type=openapi.TYPE_STRING, format='uri', example='https://yandex.ru/maps/-/CCUq4Xg~'),
                'sport_venue_type': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='ID типа площадки'),
                'region': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, description='ID региона'),
                'images': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_FILE),
                    description='Файлы изображений для загрузки (можно несколько)',
                    example=['image1.jpg', 'image2.png']
                ),
            }
        ),
        responses={
            201: openapi.Response('Площадка создана успешно', SportVenueReadSerializer),
            400: 'Ошибка валидации',
            403: 'Доступ запрещен'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if self.request.user.role != Role.OWNER:
            raise permissions.PermissionDenied("Только владельцы могут создавать площадки")
        
        sport_venue = serializer.save(owner=self.request.user)
        
        # Handle image uploads if any
        if hasattr(self.request, 'FILES') and self.request.FILES:
            images = self.request.FILES.getlist('images')
            for image_file in images:
                SportVenueImage.objects.create(sport_venue=sport_venue, image=image_file)

    def perform_update(self, serializer):
        if self.request.user.role != Role.OWNER or serializer.instance.owner != self.request.user:
            raise permissions.PermissionDenied("Вы можете обновлять только свои площадки")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != Role.OWNER or instance.owner != self.request.user:
            raise permissions.PermissionDenied("Вы можете удалять только свои площадки")
        instance.delete()

    # @action(detail=True, methods=['delete'])
    # def remove_image(self, request, pk=None):
    #     sport_venue = self.get_object()
    #     if request.user.role != Role.OWNER or sport_venue.owner != request.user:
    #         raise permissions.PermissionDenied("Можно удалять фото только у своих площадок")

    #     image_id = request.data.get('image_id')
    #     try:
    #         image = sport_venue.images.get(id=image_id)
    #         image.delete()
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #     except SportVenueImage.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
        


@csrf_exempt_api
class OwnerBookingViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    """Для владельцев: список и управление бронированиями их площадок"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        Booking.update_expired_bookings()
        if not user.is_authenticated or user.role != Role.OWNER:
            return Booking.objects.none()
        return self.queryset.filter(sport_venue__owner=user)

    @swagger_auto_schema(
        operation_description="Подтвердить бронирование (только для владельца своей площадки)",
        responses={
            200: BookingSerializer,
            400: "Невозможно подтвердить",
            403: "Нет доступа"
        }
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()

        if booking.sport_venue.owner != request.user:
            return Response({"detail": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

        if booking.status != 'PENDING':
            return Response({"detail": "Можно подтвердить только ожидающие"}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'CONFIRMED'
        booking.save()
        return Response(BookingSerializer(booking).data)

    @swagger_auto_schema(
        operation_description="Отменить бронирование (только для владельца своей площадки)",
        responses={
            200: BookingSerializer,
            400: "Невозможно отменить",
            403: "Нет доступа"
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        if booking.sport_venue.owner != request.user:
            return Response({"detail": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

        if booking.status not in ['PENDING', 'CONFIRMED']:
            return Response({"detail": "Можно отменять только ожидающие или подтвержденные"}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'CANCELLED'
        booking.save()
        return Response(BookingSerializer(booking).data)
