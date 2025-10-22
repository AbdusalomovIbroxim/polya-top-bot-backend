from rest_framework import serializers
import uuid
from .models import FootballExperience, FootballFrequency, FootballPosition, FootballFormat, User
from django.conf import settings
from django.core.files.base import ContentFile
from .utils import check_telegram_auth
import requests
import re

class UserSerializer(serializers.ModelSerializer):
    football_formats = serializers.MultipleChoiceField(
        choices=FootballFormat.choices,
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
    football_formats = serializers.ListField(
        child=serializers.ChoiceField(choices=FootballFormat.choices),
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
    
    # # --- Добавьте этот метод ---
    # def to_internal_value(self, data):
    #     # Вызываем родительский метод, чтобы выполнить стандартную валидацию
    #     # и преобразование, включая MultipleChoiceField, которое вернет 'set'
    #     internal_value = super().to_internal_value(data)

    #     # Если поле football_formats присутствует в данных и является 'set',
    #     # преобразуем его обратно в 'list'
    #     if 'football_formats' in internal_value:
    #         # Преобразование set в list (это и устраняет ошибку)
    #         internal_value['football_formats'] = list(internal_value['football_formats'])
            
    #     return internal_value
    # # --------------------------


def slugify_cyrillic(text):
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    text = text.lower()
    for cyr, lat in translit_map.items():
        text = text.replace(cyr, lat)
    text = re.sub(r'[^a-z0-9\s]+', '', text).strip().replace(' ', '_')
    text = re.sub(r'_+', '_', text)
    return text



class RegisterSerializer(serializers.ModelSerializer):
    initData = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "language", "city", "football_experience",
            "football_frequency", "football_competitions",
            "football_formats", "football_position", "initData"
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

        # --- Логика генерации username ---
        # 1. Приоритет — username из Telegram
        # 2. Если его нет, генерируем из full_name (first_name + last_name)
        # 3. Если и full_name нет, используем user_{telegram_id}
        
        username_from_telegram = user_data.get("username")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # 1. Если есть username из Telegram, используем его
        if username_from_telegram:
            validated_data["username"] = username_from_telegram
        # 2. Если нет, но есть имя или фамилия, генерируем из них
        elif first_name or last_name:
            full_name = f"{first_name} {last_name}".strip()
            # Транслитерируем и очищаем имя
            generated_username = slugify_cyrillic(full_name)
            # Добавляем суффикс, чтобы гарантировать уникальность
            validated_data["username"] = f"{generated_username}_{telegram_id}"
        # 3. Если ничего нет, используем fallback
        else:
            validated_data["username"] = f"user_{telegram_id}"

        
        # --- Извлекаем и сохраняем другие данные из Telegram ---
        validated_data["first_name"] = user_data.get("first_name", "")
        validated_data["last_name"] = user_data.get("last_name", "")
        validated_data["language"] = user_data.get("language_code", "ru")
        
        # Пароль всегда будет сгенерирован, так как он не приходит с клиента
        validated_data["password"] = uuid.uuid4().hex

        # Создаём пользователя
        user = User.objects.create_user(**validated_data)
        
        # --- Обработка фотографии ---
        photo_url = user_data.get("photo_url")
        if photo_url:
            try:
                # Отправляем HTTP-запрос для скачивания изображения
                response = requests.get(photo_url, stream=True, timeout=5)
                response.raise_for_status()
                
                # Создаём имя файла
                filename = f'tg_photo_{user.telegram_id}.jpg'
                
                # Создаём объект ContentFile из скачанного содержимого
                content = ContentFile(response.content)
                
                # Присваиваем файл полю photo и сохраняем
                user.photo.save(filename, content, save=True)
                
            except (requests.RequestException, Exception) as e:
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
