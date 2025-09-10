from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny

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
        logger.info("Login request data: %s", request.data)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        init_data = serializer.validated_data["initData"]
        parsed = check_telegram_auth(init_data, settings.TELEGRAM_BOT_TOKEN)
        if not parsed:
            return Response({"error": "Некорректная подпись Telegram"}, status=status.HTTP_403_FORBIDDEN)

        user_json = parsed.get("user")
        telegram_id = user_json.get("id") if user_json else None
        if not telegram_id:
            return Response({"error": "Нет user[id] в initData"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не зарегистрирован"}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)




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