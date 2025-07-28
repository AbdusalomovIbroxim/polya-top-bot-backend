from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Booking
from .serializers import BookingSerializer
from djangoProject.utils import csrf_exempt_api


class IsAuthenticatedOrAdmin(BasePermission):
    """
    Разрешает доступ только авторизованным пользователям и админам.
    """
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
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    permission_classes = [IsAuthenticatedOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Админы видят все бронирования
        if user.role == 'admin':
            return queryset

        # Продавцы видят бронирования своих площадок
        if user.role == 'seller':
            return queryset.filter(sport_venue__company=user)

        # Обычные пользователи видят только свои бронирования
        user_bookings = queryset.filter(user=user)
        print(f"User {user.username} (role: {user.role}) - found {user_bookings.count()} bookings")
        return user_bookings

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Подтвердить бронирование (только для продавца или админа)",
        responses={
            200: "Успешно подтверждено",
            400: "Невозможно подтвердить",
            403: "Нет доступа"
        }
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()

        if request.user.role not in ['admin', 'seller'] or \
           (request.user.role == 'seller' and booking.sport_venue.company != request.user):
            return Response(
                {"detail": "У вас нет прав на подтверждение этого бронирования"},
                status=status.HTTP_403_FORBIDDEN
            )

        if booking.status != 'PENDING':
            return Response(
                {"detail": "Можно подтверждать только ожидающие бронирования"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'CONFIRMED'
        booking.save()
        return Response(BookingSerializer(booking).data)

    @swagger_auto_schema(
        operation_description="Отменить бронирование (пользователь, продавец или админ)",
        responses={
            200: "Успешно отменено",
            400: "Невозможно отменить",
            403: "Нет доступа"
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        if request.user not in [booking.user, booking.sport_venue.company] and request.user.role != 'admin':
            return Response(
                {"detail": "У вас нет прав на отмену этого бронирования"},
                status=status.HTTP_403_FORBIDDEN
            )

        if booking.status not in ['PENDING', 'CONFIRMED']:
            return Response(
                {"detail": "Можно отменять только ожидающие или подтвержденные бронирования"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'CANCELLED'
        booking.save()
        return Response(BookingSerializer(booking).data)

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
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить бронирование",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sport_venue': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID спортивной площадки'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время начала'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время окончания'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Статус бронирования')
            }
        ),
        responses={
            200: "Обновленное бронирование",
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частично обновить бронирование",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sport_venue': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID спортивной площадки'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время начала'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Дата и время окончания'),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='Статус бронирования')
            }
        ),
        responses={
            200: "Обновленное бронирование",
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить бронирование",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
