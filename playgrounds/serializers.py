from rest_framework import serializers
from .models import SportVenue, SportVenueImage, FavoriteSportVenue, SportVenueType, Region
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta
from django.utils import timezone
from accounts.models import Role


class SportVenueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportVenueImage
        fields = '__all__'


class SportVenueSerializer(serializers.ModelSerializer):
    images = SportVenueImageSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = SportVenue
        fields = '__all__'

    def validate_owner_id(self, value):
        from accounts.models import User
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь-владелец не найден")
        if getattr(user, 'role', None) != Role.OWNER:
            raise serializers.ValidationError("Владелец должен иметь роль 'owner'")
        return value

    # def validate_type(self, value):
    #     valid_types = ['FOOTBALL', 'BASKETBALL', 'TENNIS', 'VOLLEYBALL', 'OTHER']
    #     if value and value not in valid_types:
    #         raise serializers.ValidationError(f"Type must be one of: {', '.join(valid_types)}")
    #     return value


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
    sport_venue_details = SportVenueSerializer(source='sport_venue', read_only=True)
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
