
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer, UpdateUserSerializer


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить информацию о текущем пользователе",
        responses={200: UserSerializer()}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить информацию о текущем пользователе",
        request_body=UpdateUserSerializer,
        responses={
            200: UserSerializer(),
            400: "Ошибка валидации"
        }
    )
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        serializer = UpdateUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(
            {'error': 'Ошибка валидации данных', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class TelegramAuthView(APIView):
    authentication_classes = []  # без токена
    permission_classes = []      # доступно всем

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

class TelegramAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Авторизация через Telegram",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["id", "auth_date", "hash"],
            properties={
                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Telegram ID"),
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="Telegram username"),
                "first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя"),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия"),
                "hash": openapi.Schema(type=openapi.TYPE_STRING, description="Подпись от Telegram"),
            },
            example={
                "id": 123456789,
                "username": "ibroxim",
                "first_name": "Ibroxim",
                "last_name": "Abdusalomov",
                "hash": "b4f9e2dbf2c1a74d8328f8f1f9f3df5b"
            }
        ),
        responses={200: "JWT токены и данные пользователя"}
    )
    def post(self, request):
        data = request.data.copy()

        from .utils import verify_telegram_auth
        if not verify_telegram_auth(data):
            return Response({"error": "Invalid auth data"}, status=status.HTTP_400_BAD_REQUEST)

        telegram_id = data.get("id")
        username = data.get("username")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username or f"tg_{telegram_id}",
                "first_name": first_name,
                "last_name": last_name,
            }
        )

        # JWT токен
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        })
