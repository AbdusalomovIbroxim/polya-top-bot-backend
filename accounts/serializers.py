from rest_framework import serializers
from .models import User, Booking
from playground.serializers import SportFieldSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'role', 'username', 'first_name', 'last_name',
                  'phone', 'avatar', 'rating', 'telegram_id', 'created_at', 'updated_at')
        read_only_fields = ('rating', 'created_at', 'updated_at', 'telegram_id')


class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    field = SportFieldSerializer(read_only=True)
    field_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'user', 'field', 'field_id', 'date', 'start_time', 'end_time',
                  'status', 'total_price', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at', 'total_price', 'user')
