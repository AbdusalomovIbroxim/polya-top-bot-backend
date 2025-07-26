from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# Закомментированные старые сериализаторы
"""
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'date_joined', 'photo')
        read_only_fields = ('date_joined',)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'phone', 'photo')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
"""

# Новые сериализаторы для системы авторизации по телефону/username
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'phone', 'first_name', 'last_name', 'date_joined', 'photo', 'role')
        read_only_fields = ('date_joined', 'role')


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(
        label='Логин',
        help_text='Введите номер телефона или username'
    )
    password = serializers.CharField(
        label='Пароль',
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')

        if login and password:
            # Пытаемся найти пользователя по username или телефону
            try:
                user = User.objects.get(username=login)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(phone=login)
                except User.DoesNotExist:
                    raise serializers.ValidationError('Пользователь с таким логином не найден.')

            # Проверяем пароль
            user = authenticate(username=user.username, password=password)
            if not user:
                raise serializers.ValidationError('Неверный пароль.')
            
            if not user.is_active:
                raise serializers.ValidationError('Пользователь заблокирован.')

            attrs['user'] = user
        else:
            raise serializers.ValidationError('Необходимо указать логин и пароль.')

        return attrs

    def to_representation(self, instance):
        user = instance['user']
        refresh = RefreshToken.for_user(user)
        
        return {
            'message': 'Успешная авторизация',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'phone', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким username уже существует.')
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Пользователь с таким номером телефона уже существует.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError('Пароли не совпадают.')

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        
        return {
            'message': 'Пользователь успешно зарегистрирован',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(instance).data
        } 