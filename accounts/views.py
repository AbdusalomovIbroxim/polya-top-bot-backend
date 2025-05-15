from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from .serializers import UserSerializer, UserCreateSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import hashlib
import hmac
import json
from django.conf import settings

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

class TelegramAuthView(APIView):
    def post(self, request):
        try:
            init_data = request.data.get('initData')
            if not init_data:
                return Response({'error': 'No initData provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Verify the data from Telegram
            data_check_string = '\n'.join(sorted(init_data.split('&')))
            secret_key = hmac.new(
                "WebAppData".encode(),
                settings.TELEGRAM_BOT_TOKEN.encode(),
                hashlib.sha256
            ).digest()
            
            hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
            
            if hash != init_data.split('hash=')[1]:
                return Response({'error': 'Invalid hash'}, status=status.HTTP_400_BAD_REQUEST)

            # Parse user data
            user_data = json.loads(init_data.split('user=')[1].split('&')[0])
            
            # Get or create user
            user, created = User.objects.get_or_create(
                telegram_id=user_data['id'],
                defaults={
                    'username': f"tg_{user_data['id']}",
                    'telegram_username': user_data.get('username', ''),
                    'telegram_first_name': user_data.get('first_name', ''),
                    'telegram_last_name': user_data.get('last_name', ''),
                }
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'telegram_username': user.telegram_username,
                    'first_name': user.telegram_first_name,
                    'last_name': user.telegram_last_name,
                    'role': user.role,
                }
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
