from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, mixins
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import SportVenue, SportVenueType, Region, FavoriteSportVenue
from .serializers import (
    SportVenueSerializer,
    SportVenueTypeSerializer,
    RegionSerializer,
    FavoriteSportVenueSerializer
)

class SportVenueTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SportVenueType.objects.all()
    serializer_class = SportVenueTypeSerializer
    permission_classes = [permissions.AllowAny]

class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]

class ClientSportVenueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SportVenue.objects.all().prefetch_related('images', 'sport_venue_type', 'region')
    serializer_class = SportVenueSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sport_venue_type', 'region', 'city']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['price_per_hour', 'name']

    @swagger_auto_schema(
        operation_description="Проверить доступность площадки на определённую дату",
        manual_parameters=[
            openapi.Parameter(
                'date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date',
                description='Дата в формате YYYY-MM-DD', required=True
            )
        ]
    )
    @action(detail=True, methods=['get'], url_path='available-time')
    def available_time(self, request, pk=None):
        sport_venue = self.get_object()
        date_str = request.query_params.get('date')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date < timezone.now().date():
                return Response({'error': 'Нельзя проверять дату в прошлом'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Неверный формат даты. Используйте YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        # Время работы из базы
        open_time = sport_venue.open_time
        close_time = sport_venue.close_time

        start_day = timezone.make_aware(datetime.combine(date, open_time))
        end_day = timezone.make_aware(datetime.combine(date, close_time))

        # Берём все события на это поле, которые пересекаются с рабочими часами
        events = Event.objects.filter(
            field=sport_venue,
            start_game_time__lt=end_day,
            start_game_time__gte=start_day
        )

        booked = set()
        for event in events:
            event_start = event.start_game_time
            event_end = event_start + timedelta(hours=event.game_time)
            current = event_start
            while current < event_end:
                booked.add(timezone.localtime(current).strftime('%H:%M'))
                current += timedelta(hours=1)

        # Формируем слоты по часам
        slots = []
        current = datetime.combine(date, open_time)
        end = datetime.combine(date, close_time)
        while current < end:
            aware_time = timezone.make_aware(current)
            time_str = timezone.localtime(aware_time).strftime('%H:%M')
            is_available = aware_time > timezone.now() if date == timezone.now().date() else True
            slots.append({'time': time_str, 'is_available': is_available and time_str not in booked})
            current += timedelta(hours=1)

        return Response({
            'date': date_str,
            'working_hours': {'start': open_time.strftime('%H:%M'), 'end': close_time.strftime('%H:%M')},
            'time_points': slots
        })
        
class FavoriteSportVenueViewSet(
    mixins.ListModelMixin,       # GET /favorites/
    mixins.CreateModelMixin,     # POST /favorites/
    mixins.DestroyModelMixin,    # DELETE /favorites/{id}/
    viewsets.GenericViewSet
):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return FavoriteSportVenue.objects.none()
        return FavoriteSportVenue.objects.filter(user=self.request.user).select_related("sport_venue")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



def welcome(request):
    return render(request, "index.html")

def custom_page_not_found_view(request, exception):
    return render(request, "404.html", status=404)