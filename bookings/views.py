from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from .models import Booking
from .serializers import BookingSerializer
from drf_yasg.utils import swagger_auto_schema
from djangoProject.utils import csrf_exempt_api
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class BookingFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="start_time", lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name="end_time", lookup_expr='lte')
    status = filters.CharFilter(field_name="status")
    playground = filters.NumberFilter(field_name="playground__id")
    user = filters.NumberFilter(field_name="user__id")

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'status', 'playground', 'user']

@csrf_exempt_api
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_authenticated and user.role == 'admin':
            return queryset

        if user.is_authenticated and user.role == 'seller':
            return queryset.filter(playground__company=user)

        if user.is_authenticated:
            return queryset.filter(user=user)
            
        return queryset.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            # Для неавторизованных пользователей сохраняем ключ сессии
            if not self.request.session.session_key:
                self.request.session.create()
            serializer.save(session_key=self.request.session.session_key)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        
        # Проверяем права на подтверждение
        if request.user.role not in ['admin', 'seller'] or \
           (request.user.role == 'seller' and booking.playground.company != request.user):
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

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Проверяем права на отмену
        if request.user not in [booking.user, booking.playground.company] and request.user.role != 'admin':
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
        responses={
            201: BookingSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает список всех доступных бронирований",
        responses={
            200: BookingSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Возвращает детальную информацию о конкретном бронировании",
        responses={
            200: BookingSerializer,
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
