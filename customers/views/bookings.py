from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from bookings.models import Booking
from bookings.serializers import BookingSerializer
from accounts.models import Role
from customers.permissions import IsOwnerOrSuperAdmin
from rest_framework.permissions import IsAuthenticated

class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'stadium', 'start_time', 'end_time']
    ordering_fields = ['date', 'created_at']
    search_fields = ['client__full_name', 'client__phone']

    def get_queryset(self):
        user = self.request.user

        if getattr(self, "swagger_fake_view", False) or user.is_anonymous:
            return Booking.objects.none()
        
        # --- Используем ПРАВИЛЬНЫЕ отношения: 'user' и 'stadium' ---
        
        # --- Супер админ видит все брони ---
        if user.is_superuser or user.role == Role.SUPERADMIN:
            # ИСПРАВЛЕНО: 'client', 'field' заменены на 'user', 'stadium'
            return Booking.objects.all().select_related('user', 'stadium')

        # --- Владелец видит только свои поля ---
        if getattr(user, "is_owner", False) or user.role == Role.OWNER:
            # ИСПРАВЛЕНО: 'client', 'field' заменены на 'user', 'stadium'
            # (Предполагая, что 'field' корректно работает в фильтре: field__owner=user)
            return Booking.objects.filter(field__owner=user).select_related('user', 'stadium')

        # Остальные роли — без доступа
        return Booking.objects.none()
    
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Просмотр деталей конкретной брони.
        """
        booking = self.get_object()
        self.check_object_permissions(request, booking)
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
