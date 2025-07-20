from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserCreateSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import hashlib
import hmac
import json
from urllib.parse import parse_qs, urlparse
from django.conf import settings
from djangoProject.utils import check_webapp_signature

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
        operation_description="Получить текущего пользователя",
        responses={200: UserSerializer},
        methods=['get']
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить данные текущего пользователя",
        request_body=UserSerializer,
        responses={200: UserSerializer},
        methods=['put', 'patch']
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class TelegramAuthViewSet(viewsets.ViewSet):
    """
    ViewSet для авторизации через Telegram Web App
    """
    
    def _verify_telegram_data(self, init_data):
        """
        Проверяет подлинность данных от Telegram Web App
        """
        try:
            # Используем правильную функцию проверки подписи
            if not settings.TELEGRAM_BOT_TOKEN:
                print('TELEGRAM_BOT_TOKEN is empty or not set')
                return False, "Telegram bot token not configured"
            
            print('Using TELEGRAM_BOT_TOKEN:', settings.TELEGRAM_BOT_TOKEN[:10] + '...' if len(settings.TELEGRAM_BOT_TOKEN) > 10 else settings.TELEGRAM_BOT_TOKEN)
            print('FULL TELEGRAM_BOT_TOKEN (for debugging):', settings.TELEGRAM_BOT_TOKEN)
            print('About to call check_webapp_signature with init_data:', init_data[:100] + '...' if len(init_data) > 100 else init_data)
            
            is_valid = check_webapp_signature(settings.TELEGRAM_BOT_TOKEN, init_data)
            print('check_webapp_signature returned:', is_valid)
            
            if is_valid:
                # Парсим данные для извлечения информации о пользователе
                parsed_data = parse_qs(init_data)
                return True, parsed_data
            else:
                return False, "Hash verification failed"
                
        except Exception as e:
            print('Exception in _verify_telegram_data:', str(e))
            return False, f"Error verifying data: {str(e)}"
    
    def _extract_user_data(self, parsed_data):
        """
        Извлекает данные пользователя из Telegram данных
        """
        user_data = parsed_data.get('user', [None])[0]
        if user_data:
            try:
                return json.loads(user_data)
            except json.JSONDecodeError:
                return None
        return None
    
    @swagger_auto_schema(
        operation_description="Авторизация через Telegram Web App",
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
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
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
        Авторизация через Telegram Web App
        """
        init_data = request.data.get('init_data')
        if not init_data:
            return Response(
                {'error': 'init_data is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем подлинность данных через utils
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
        
        # Получаем или создаем пользователя
        telegram_id = user_data.get('id')
        username = user_data.get('username')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        
        if not telegram_id:
            return Response(
                {'error': 'Telegram ID not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ищем пользователя по telegram_id
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            # Создаем нового пользователя
            username = username or f"tg_{telegram_id}"
            email = f"{telegram_id}@telegram.user"
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                telegram_id=telegram_id,
                telegram_username=username,
                telegram_first_name=first_name,
                telegram_last_name=last_name,
                role=User.Role.USER  # По умолчанию обычный пользователь
            )
        
        # Генерируем JWT токены
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'telegram_id': user.telegram_id
            }
        })
