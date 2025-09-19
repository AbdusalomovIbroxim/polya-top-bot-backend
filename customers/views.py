from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone

from bookings.models import Booking, Transaction
from playgrounds.models import SportVenue
from playgrounds.serializers import SportVenueSerializer
from bookings.serializers import BookingSerializer, TransactionSerializer


# 🔹 Владелец может управлять только своими площадками
class OwnerVenueViewSet(viewsets.ModelViewSet):
    serializer_class = SportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return SportVenue.objects.none()
        return SportVenue.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# 🔹 Владелец может видеть бронирования только по своим площадкам
class OwnerBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated:
            return Booking.objects.none()
        return (
            Booking.objects.filter(stadium__venue__owner=self.request.user)
            .select_related("stadium", "user")
        )


# 🔹 Владелец видит только транзакции по своим площадкам
class OwnerTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated:
            return Transaction.objects.none()
        return Transaction.objects.filter(
            booking__stadium__venue__owner=self.request.user
        ).select_related("booking", "user")


# 🔹 Статистика для владельца
class OwnerStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if getattr(self, "swagger_fake_view", False):
            return Response({})

        bookings = Booking.objects.filter(stadium__venue__owner=request.user)
        transactions = Transaction.objects.filter(booking__stadium__venue__owner=request.user)

        # Подсчет бронирований и участников (у каждого booking есть user → считаем брони)
        stats = bookings.aggregate(
            total_bookings=Count("id"),
            upcoming_bookings=Count("id", filter=models.Q(start_time__gte=timezone.now())),
            total_income=Sum("amount"),
        )

        data = {
            "total_bookings": stats["total_bookings"] or 0,
            "total_income": stats["total_income"] or 0,
            "upcoming_bookings": stats["upcoming_bookings"] or 0,
            "total_transactions": transactions.count(),
        }
        return Response(data)
