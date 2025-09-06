from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
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

class FavoriteSportVenueViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSportVenueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteSportVenue.objects.filter(user=self.request.user).select_related('sport_venue')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['delete'], url_path='remove')
    def remove(self, request, pk=None):
        favorite = self.get_object()
        favorite.delete()
        return Response({"detail": "Удалено из избранного"}, status=204)


def welcome(request):
    return render(request, "index.html")

def custom_page_not_found_view(request, exception):
    return render(request, "404.html", status=404)