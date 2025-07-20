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
from djangoProject.utils import check_webapp_signature
from accounts.models import User

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @swagger_auto_schema(
        operation_description="Создать нового пользователя",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: "Bad Request"}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить список всех пользователей",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить информацию о пользователе",
        responses={200: UserSerializer, 404: "Not Found"}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Полностью обновить пользователя",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 404: "Not Found"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частично обновить пользователя",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 404: "Not Found"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить пользователя",
        responses={204: "No Content", 404: "Not Found"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить текущего пользователя через Telegram Web App",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['init_data'],
            properties={
                'init_data': openapi.Schema(type=openapi.TYPE_STRING, description='Данные инициализации от Telegram Web App')
            }
        ),
        responses={200: UserSerializer},
        methods=['post']
    )
    @action(detail=False, methods=['post'], permission_classes=[TelegramWebAppPermission])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить данные текущего пользователя через Telegram Web App",
        request_body=UserSerializer,
        responses={200: UserSerializer},
        methods=['put', 'patch']
    )
    @action(detail=False, methods=['put', 'patch'], permission_classes=[TelegramWebAppPermission])
    def update_me(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TelegramAuthViewSet(viewsets.ViewSet):
    """
    ViewSet для авторизации через Telegram Web App (без JWT токенов)
    """
    
    def _verify_telegram_data(self, init_data):
        try:
            if not settings.TELEGRAM_BOT_TOKEN:
                return False, "Telegram bot token not configured"
            is_valid = check_webapp_signature(settings.TELEGRAM_BOT_TOKEN, init_data)
            if is_valid:
                parsed_data = parse_qs(init_data)
                return True, parsed_data
            else:
                return False, "Hash verification failed"
        except Exception as e:
            return False, f"Error verifying data: {str(e)}"

    def _extract_user_data(self, parsed_data):
        user_data = parsed_data.get('user', [None])[0]
        if user_data:
            try:
                return json.loads(user_data)
            except json.JSONDecodeError:
                return None
        return None

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
        """
        Авторизация через Telegram Web App (без токенов)
        """
        init_data = request.data.get('init_data')
        if not init_data:
            return Response(
                {'error': 'init_data is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        is_valid, parsed_data = self._verify_telegram_data(init_data)
        if not is_valid:
            return Response(
                {'error': 'Hash verification failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        user_data = self._extract_user_data(parsed_data)
        if not user_data:
            return Response(
                {'error': 'User data not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        telegram_id = user_data.get('id')
        username = user_data.get('username')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        if not telegram_id:
            return Response(
                {'error': 'Telegram ID not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': username or f"tg_{telegram_id}",
                'email': f"{telegram_id}@telegram.user",
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'telegram_id': user.telegram_id,
                'photo': user.photo.url if user.photo else None
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
