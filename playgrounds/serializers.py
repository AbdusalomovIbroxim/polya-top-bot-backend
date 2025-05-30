from rest_framework import serializers
from .models import Playground, PlaygroundImage, FavoritePlayground, PlaygroundType
from accounts.serializers import UserSerializer
from datetime import datetime, timedelta
from django.utils import timezone


class PlaygroundImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaygroundImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['created_at']


class PlaygroundSerializer(serializers.ModelSerializer):
    images = PlaygroundImageSerializer(many=True, read_only=True)
    company = UserSerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Playground
        fields = ['id', 'name', 'description', 'price_per_hour', 'images', 'company', 'company_id', 'created_at',
                  'updated_at', 'city', 'address', 'latitude', 'longitude', 'deposit_amount', 'yandex_map_url']
        read_only_fields = ['created_at', 'updated_at']

    def validate_company_id(self, value):
        from accounts.models import User
        try:
            User.objects.get(id=value, role='seller')
        except User.DoesNotExist:
            raise serializers.ValidationError("Company must be a seller user")
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


class FavoritePlaygroundSerializer(serializers.ModelSerializer):
    playground_details = PlaygroundSerializer(source='playground', read_only=True)

    class Meta:
        model = FavoritePlayground
        fields = ['id', 'playground', 'playground_details', 'created_at']
        read_only_fields = ['created_at']


class PlaygroundTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaygroundType
        fields = ['id', 'name', 'description', 'icon', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
