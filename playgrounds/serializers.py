from rest_framework import serializers
from .models import SportVenue, SportVenueImage, FavoriteSportVenue, SportVenueType, Region
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta
from django.utils import timezone


class SportVenueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenueImage
        fields = '__all__'


class SportVenueReadSerializer(serializers.ModelSerializer):
    images = SportVenueImageSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)

    class Meta:
        model = SportVenue
        fields = '__all__'


class SportVenueWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenue
        exclude = ['owner']


class TimePointSerializer(serializers.Serializer):
    time = serializers.CharField()
    is_available = serializers.BooleanField()


class AvailabilityResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    working_hours = serializers.DictField(
        child=serializers.CharField()
    )
    time_points = TimePointSerializer(many=True)
    timezone_offset = serializers.IntegerField(required=False)


class FavoriteSportVenueSerializer(serializers.ModelSerializer):
    sport_venue_details = SportVenueReadSerializer(source='sport_venue', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteSportVenue
        fields = '__all__'


class SportVenueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenueType
        fields = ("slug", "name")


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
