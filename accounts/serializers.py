from rest_framework import serializers
import uuid
from .models import FootballExperience, FootballFrequency, FootballPosition, FootballFormat, User

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
        fields = ("language", "city", "username", "football_experience", "football_frequency", "football_competitions", "football_formats", "football_position", "telegram_id", "password", "initData")

    def create(self, validated_data):
        import uuid
        from django.conf import settings
        from .utils import check_telegram_auth

        init_data = validated_data.pop("initData", None)
        telegram_id = validated_data.get("telegram_id")

        # Если прилетел initData — проверяем и заполняем телеграм-поля
        if init_data:
            parsed = check_telegram_auth(init_data, settings.TELEGRAM_BOT_TOKEN)
            if not parsed:
                raise serializers.ValidationError({"initData": "Некорректная подпись Telegram"})
            
            if "user[id]" in parsed:
                validated_data["telegram_id"] = parsed["user[id]"]
            if "user[username]" in parsed:
                validated_data.setdefault("username", parsed["user[username]"])

        # генерируем пароль (если не пришёл)
        if "password" not in validated_data or not validated_data["password"]:
            validated_data["password"] = uuid.uuid4().hex

        user = User.objects.create_user(**validated_data)
        return user



class LoginSerializer(serializers.Serializer):
    initData = serializers.CharField()

    
    
    

class ChoiceSerializer(serializers.Serializer):
    """
    Сериализатор общего назначения для преобразования
    классов TextChoices в список объектов.
    """
    value = serializers.CharField(source='0')
    display_name = serializers.CharField(source='1')

def get_choices_from_enum(enum_class):
    """
    Вспомогательная функция для получения списка словарей
    из класса TextChoices.
    """
    return [{'value': choice[0], 'display_name': choice[1]} for choice in enum_class.choices]
