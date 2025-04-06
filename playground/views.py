from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import SportField
from .serializers import SportFieldSerializer



class SportFieldViewSet(viewsets.ModelViewSet):
    queryset = SportField.objects.all()
    serializer_class = SportFieldSerializer
    permission_classes = [AllowAny]  # Временно разрешаем все операции для тестов
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sport_type', 'region', 'district', 'is_indoor']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['price_per_hour', 'rating', 'created_at']
    ordering = ['-created_at']
