from rest_framework import serializers
import uuid
from .models import FootballExperience, FootballFrequency, FootballPosition, FootballFormat, User
from django.conf import settings
from django.core.files.base import ContentFile
from .utils import check_telegram_auth
import requests


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

        user_data = parsed.get("user")
        if not user_data or "id" not in user_data:
            raise serializers.ValidationError({"initData": "Нет user.id в initData"})

        telegram_id = user_data["id"]
        validated_data["telegram_id"] = telegram_id

        if not validated_data.get("username"):
            validated_data["username"] = user_data.get("username") or f"user_{telegram_id}"
            
        first_name = user_data.get("first_name")
        if first_name:
            validated_data["first_name"] = first_name
            
        last_name = user_data.get("last_name")
        if last_name:
            validated_data["last_name"] = last_name

        # username — приоритет от клиента, если не передан → берём из Telegram
        if not validated_data.get("username"):
            validated_data["username"] = user_data.get("username") or f"user_{telegram_id}"

        # если пароль не передали → создаём случайный
        if not validated_data.get("password"):
            validated_data["password"] = uuid.uuid4().hex

        user = User.objects.create_user(**validated_data)
        
        photo_url = user_data.get("photo_url")
        if photo_url:
            try:
                # Отправляем HTTP-запрос для скачивания изображения
                response = requests.get(photo_url, stream=True, timeout=5)
                response.raise_for_status()  # Выбросит исключение для HTTP-ошибок
                
                # Создаём имя файла
                filename = f'tg_photo_{user.telegram_id}.jpg'
                
                # Создаём объект ContentFile из скачанного содержимого
                content = ContentFile(response.content)
                
                # Присваиваем файл полю photo и сохраняем
                user.photo.save(filename, content, save=True)
            except (requests.RequestException, Exception) as e:
                # Обработка ошибок, если не удалось скачать или сохранить фото
                print(f"Ошибка при загрузке фото из Telegram: {e}")
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
