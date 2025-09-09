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
    initData = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "language", "city", "username",
            "football_experience", "football_frequency",
            "football_competitions", "football_formats", "football_position",
            "telegram_id", "password", "initData"
        )
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "telegram_id": {"read_only": True},  # чтобы клиент не подменял
        }

    def create(self, validated_data):
        init_data = validated_data.pop("initData")
        parsed = check_telegram_auth(init_data, settings.TELEGRAM_BOT_TOKEN)
        if not parsed:
            raise serializers.ValidationError({"initData": "Некорректная подпись Telegram"})

        telegram_id = parsed.get("user[id]")
        if not telegram_id:
            raise serializers.ValidationError({"initData": "Нет user[id] в initData"})

        validated_data["telegram_id"] = telegram_id

        if "user[username]" in parsed and not validated_data.get("username"):
            validated_data["username"] = parsed["user[username]"]

        if not validated_data.get("password"):
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
