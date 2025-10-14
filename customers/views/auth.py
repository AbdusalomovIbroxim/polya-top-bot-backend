from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
import logging

from accounts.models import User
from accounts.serializers import UserSerializer, LoginSerializer
from accounts.utils import check_telegram_auth
from django.conf import settings

logger = logging.getLogger(__name__)


class AdminAuthViewSet(viewsets.ViewSet):
    """
    Авторизация для админ-панели:
    доступна только владельцам (owner) и супер-админам (superadmin).
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Логин владельца или супер-админа по initData (Telegram WebApp)",
        request_body=LoginSerializer,
        responses={200: UserSerializer()}
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        authentication_classes=[],
    )
    def login(self, request):
        logger.info("Получен запрос на /admin/auth/login/")

        init_data = request.data.get("initData")
        if not init_data:
            return Response(
                {"error": "initData не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info("Проверка initData...")
        auth_result = check_telegram_auth(init_data, settings.TELEGRAM_BOT_TOKEN)

        if not auth_result:
            logger.warning("Авторизация не пройдена. Некорректные данные Telegram.")
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
            user = User.objects.get(telegram_id=telegram_id)
            logger.info("Пользователь с telegram_id=%s найден", telegram_id)
        except User.DoesNotExist:
            logger.warning("Пользователь не найден в базе (telegram_id=%s)", telegram_id)
            return Response(
                {"error": "Пользователь не найден или не зарегистрирован"},
                status=status.HTTP_404_NOT_FOUND
            )

        # --- Проверка роли (только owner и superadmin) ---
        allowed_roles = ["owner", "superadmin"]
        if user.role not in allowed_roles:
            logger.warning("Доступ запрещен: роль '%s' не входит в список разрешенных", user.role)
            return Response(
                {"error": "Доступ запрещен. Только владельцы и супер-админы могут войти."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --- Генерация JWT токенов ---
        refresh = RefreshToken.for_user(user)
        logger.info("Авторизация успешна (роль=%s)", user.role)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)
