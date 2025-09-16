from rest_framework import serializers
from .models import SportVenue, SportVenueType, Region, SportVenueImage, FavoriteSportVenue


class SportVenueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenueImage
        fields = ['id', 'image']


class SportVenueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenueType
        fields = ['id', 'name', 'slug']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'slug']


class SportVenueSerializer(serializers.ModelSerializer):
    sport_venue_type = SportVenueTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    images = SportVenueImageSerializer(many=True, read_only=True)

    class Meta:
        model = SportVenue
        fields = [
            'id', 'name', 'description', 'price_per_hour',
            'city', 'address', 'latitude', 'longitude', 'yandex_map_url',
            'sport_venue_type', 'region', 'open_time', 'close_time','owner', 'images'
        ]


class FavoriteSportVenueSerializer(serializers.ModelSerializer):
    sport_venue = SportVenueSerializer(read_only=True)
    sport_venue_id = serializers.PrimaryKeyRelatedField(
        queryset=SportVenue.objects.all(),
        source='sport_venue',
        write_only=True
    )

    class Meta:
        model = FavoriteSportVenue
        fields = ['id', 'sport_venue', 'sport_venue_id', 'created_at']
