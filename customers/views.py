from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes


from playgrounds.models import SportVenue
from bookings.models import Booking, Transaction
from playgrounds.serializers import SportVenueSerializer
from bookings.serializers import BookingSerializer, TransactionSerializer
from .services import get_financial_summary, get_venue_usage, get_user_activity


# 🔹 Кастомные permissions
class IsOwner(BasePermission):
    """Доступ только владельцу поля"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, "is_owner") and request.user.is_owner


class IsSuperAdminOrOwner(BasePermission):
    """Доступ супер-админу или владельцу"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (getattr(request.user, "is_superuser", False) or getattr(request.user, "is_owner", False))


# 🔹 Владелец может управлять только своими площадками
class OwnerVenueViewSet(viewsets.ModelViewSet):
    serializer_class = SportVenueSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return SportVenue.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(owner=self.request.user)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 🔹 Владелец видит только бронирования своих площадок
class OwnerBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Booking.objects.filter(stadium__venue__owner=self.request.user).select_related("stadium", "user")


# 🔹 Владелец видит только свои транзакции
class OwnerTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Transaction.objects.filter(
            booking__stadium__venue__owner=self.request.user
        ).select_related("booking", "user")


# 🔹 Аналитика для владельца
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOwner])
def owner_analytics(request):
    owner = request.user
    try:
        data = {
            "financial_summary": get_financial_summary(owner),
            "venue_usage": get_venue_usage(owner, "month"),
            "user_activity": get_user_activity(owner, "month"),
        }
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
