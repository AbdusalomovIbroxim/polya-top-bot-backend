from rest_framework import serializers
from .models import User, FootballFormat
import uuid

class UserSerializer(serializers.ModelSerializer):
    football_formats = serializers.MultipleChoiceField(
        choices=User._meta.get_field("football_formats").choices,
        required=False
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'phone',
            'photo',
            'role',
            'language',
            'city',
            'football_experience',
            'football_frequency',
            'football_competitions',
            'football_formats',
            'football_position',
            'date_joined',
        )
        read_only_fields = ('id', 'date_joined', 'role')


class UpdateUserSerializer(serializers.ModelSerializer):
    football_formats = serializers.MultipleChoiceField(
        choices=User._meta.get_field("football_formats").choices,
        required=False
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'phone',
            'photo',
            'language',
            'city',
            'football_experience',
            'football_frequency',
            'football_competitions',
            'football_formats',
            'football_position',
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = ("language", "city", "username", "football_experience", "football_frequency", "football_competitions", "football_formats", "football_position", "telegram_id")

    def create(self, validated_data):
        validated_data['password'] = uuid.uuid4().hex
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)