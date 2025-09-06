from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from bookings.models import SportVenue, Event, Payment
from playgrounds.serializers import SportVenueSerializer
from bookings.serializers import EventReadSerializer, PaymentSerializer

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


# 🔹 Владелец может видеть ивенты только по своим площадкам
class OwnerEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated:
            return Event.objects.none()
        return Event.objects.filter(sport_venue__owner=self.request.user).select_related("sport_venue")


# 🔹 Владелец видит только платежи по своим площадкам
class OwnerPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated:
            return Payment.objects.none()
        return Payment.objects.filter(event__sport_venue__owner=self.request.user)


# 🔹 Статистика для владельца
class OwnerStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):  
            return Response({})

        events = Event.objects.filter(sport_venue__owner=request.user)
        payments = Payment.objects.filter(event__sport_venue__owner=request.user)

        data = {
            "total_events": events.count(),
            "total_participants": sum(e.participants.count() for e in events),
            "total_income": payments.aggregate(total=Sum("amount"))["total"] or 0,
            "upcoming_events": events.filter(start_game_time__gte="now").count(),
        }
        return Response(data)
