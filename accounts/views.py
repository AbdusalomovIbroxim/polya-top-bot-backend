from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserCreateSerializer
from .permission import TelegramWebAppPermission
import json
from urllib.parse import parse_qs
from django.conf import settings
from accounts.models import User
from djangoProject.utils import check_webapp_signature, parse_telegram_init_data

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Получить текущего пользователя через Telegram Web App",
        manual_parameters=[
            openapi.Parameter(
                'init_data',
                openapi.IN_QUERY,
                description='Данные инициализации от Telegram Web App',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: UserSerializer},
        methods=['get']
    )
    @action(detail=False, methods=['get'], permission_classes=[TelegramWebAppPermission])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить данные текущего пользователя через Telegram Web App",
        request_body=UserSerializer,
        responses={200: UserSerializer},
        methods=['put', 'patch']
    )
    @action(detail=False, methods=['put', 'patch'], permission_classes=[TelegramWebAppPermission])
    def update_me(self, request):
        partial = request.method == 'PATCH'
        serializer = UserSerializer(request.user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Получить пользователя по telegram_id",
        manual_parameters=[
            openapi.Parameter('telegram_id', openapi.IN_PATH, description="Telegram ID пользователя", type=openapi.TYPE_STRING)
        ],
        responses={200: UserSerializer, 404: 'Not Found'},
        methods=['get']
    )
    @action(detail=False, methods=['get'], url_path='by_telegram_id/(?P<telegram_id>[^/]+)', permission_classes=[permissions.AllowAny])
    def by_telegram_id(self, request, telegram_id=None):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class TelegramAuthViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="Авторизация через Telegram Web App (без токенов)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['init_data'],
            properties={
                'init_data': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Данные инициализации от Telegram Web App'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешная авторизация",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'telegram_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'photo': openapi.Schema(type=openapi.TYPE_STRING, description='URL фото пользователя'),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def telegram_auth(self, request):
        init_data = request.data.get('init_data')
        if not init_data:
            return Response({'error': 'init_data is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not check_webapp_signature(settings.TELEGRAM_BOT_TOKEN, init_data):
            return Response({'error': 'Hash verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        user_data = parse_telegram_init_data(init_data)
        if not user_data:
            return Response({'error': 'User data not found'}, status=status.HTTP_400_BAD_REQUEST)
        telegram_id = user_data.get('id')
        if not telegram_id:
            return Response({'error': 'Telegram ID not found'}, status=status.HTTP_400_BAD_REQUEST)
        defaults = {
            'username': user_data.get('username') or f"tg_{telegram_id}",
            'email': f"{telegram_id}@telegram.user",
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
        }
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults=defaults
        )
        # Обновить фото, если оно есть и изменилось
        photo_url = user_data.get('photo_url')
        if photo_url and (not user.photo or getattr(user.photo, 'url', None) != photo_url):
            user.photo = photo_url  # если photo = URLField/ImageField
            user.save()
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': getattr(user, 'role', None),
                'telegram_id': user.telegram_id,
                'photo': user.photo.url if hasattr(user.photo, 'url') else user.photo if user.photo else None
            }
        })

class TelegramWebAppPermission(permissions.BasePermission):
    """
    Permission для проверки Telegram Web App hash (init_data).
    """
    def has_permission(self, request, view):
        init_data = request.data.get('init_data') or request.query_params.get('init_data')
        if not init_data:
            return False
        if not check_webapp_signature(settings.TELEGRAM_BOT_TOKEN, init_data):
            return False
        # Парсим данные и аутентифицируем пользователя
        parsed_data = dict(parse_qs(init_data))
        user_data = parsed_data.get('user', [None])[0]
        if user_data:
            try:
                user_data = json.loads(user_data)
            except Exception:
                return False
        else:
            return False
        telegram_id = user_data.get('id')
        if not telegram_id:
            return False
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return False
        request.user = user
        return True
