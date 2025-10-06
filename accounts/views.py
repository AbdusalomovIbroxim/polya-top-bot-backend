from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from urllib.parse import unquote

from accounts.models import FootballExperience, FootballFormat, FootballFrequency, FootballPosition, User
from djangoProject import settings
from .serializers import UserSerializer, UpdateUserSerializer, RegisterSerializer, LoginSerializer, get_choices_from_enum
from .utils import check_telegram_auth

import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить данные текущего пользователя",
        responses={200: UserSerializer()}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Обновить данные текущего пользователя",
        request_body=UpdateUserSerializer,
        responses={200: UserSerializer(), 400: "Ошибка валидации"}
    )
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        serializer = UpdateUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(
            {"error": "Ошибка валидации данных", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'], , permission_classes=[AllowAny])
    def check_admin_access(self, request):
        """
        Проверка, может ли пользователь получить доступ к админке.
        Входные данные: telegram_id
        """
        telegram_id = request.data.get("telegram_id")
        if not telegram_id:
            return Response({"allowed": False}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Делаем запрос к вашему серверу/базе, чтобы проверить роль
            user = request.user  # или получаем по telegram_id из базы
            # Если используете модель User с полем role и telegram_id:
            # from .models import User
            # user = User.objects.filter(telegram_id=telegram_id).first()
            if user and user.role in ["superadmin", "owner"]:
                return Response({"allowed": True})
        except Exception:
            pass

        return Response({"allowed": False})


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=RegisterSerializer,
        responses={201: UserSerializer()}
    )
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        operation_description="Логин пользователя по initData",
        request_body=LoginSerializer,
        responses={200: UserSerializer()}
    )
    @action(detail=False, methods=["post"])
    def login(self, request):
        logger.info("Получен запрос на /auth/login/")
        
        init_data = request.data.get("initData")
        if not init_data:
             return Response(
                {"error": "initData не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Проверка initData...")
        auth_result = check_telegram_auth(init_data, settings.TELEGRAM_BOT_TOKEN)

        if not auth_result:
            logger.warning("Авторизация не пройдена. Возвращаем 403 Forbidden.")
            return Response(
                {"error": "Некорректные данные авторизации Telegram."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user_data = auth_result.get("user")
        if not user_data or "id" not in user_data:
            logger.error("В данных авторизации отсутствует информация о пользователе (user.id).")
            return Response(
                {"error": "Неполные данные пользователя от Telegram."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        telegram_id = user_data["id"]

        try:
            # ИЗМЕНЕНИЕ: Ищем пользователя, но не создаем его.
            user = User.objects.get(telegram_id=telegram_id)
            logger.info("Пользователь с telegram_id: %s найден.", telegram_id)
        
        except User.DoesNotExist:
            # Если пользователь не найден, возвращаем ошибку.
            logger.warning("Попытка входа для незарегистрированного telegram_id: %s", telegram_id)
            return Response(
                {"error": "Пользователь не зарегистрирован"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.exception("Ошибка при поиске пользователя: %s", e)
            return Response(
                {"error": "Ошибка на стороне сервера при работе с базой данных."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Если пользователь найден, генерируем для него JWT токены.
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })





class FootballExperienceView(APIView):
    def get(self, request):
        choices = get_choices_from_enum(FootballExperience)
        return Response(choices)

class FootballFrequencyView(APIView):
    def get(self, request):
        choices = get_choices_from_enum(FootballFrequency)
        return Response(choices)

class FootballPositionView(APIView):
    def get(self, request):
        choices = get_choices_from_enum(FootballPosition)
        return Response(choices)

class FootballFormatView(APIView):
    def get(self, request):
        choices = get_choices_from_enum(FootballFormat)
        return Response(choices)

class FootballChoicesView(APIView):
    
    def get(self, request):
        data = {
            'experience': get_choices_from_enum(FootballExperience),
            'frequency': get_choices_from_enum(FootballFrequency),
            'position': get_choices_from_enum(FootballPosition),
            'format': get_choices_from_enum(FootballFormat),
        }
        return Response(data)
    
    
