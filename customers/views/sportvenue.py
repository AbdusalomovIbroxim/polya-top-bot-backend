from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from playgrounds.models import SportVenue
from playgrounds.serializers import SportVenueSerializer
from ..permissions import IsOwnerOrSuperAdmin
from rest_framework import viewsets, status
from rest_framework.response import Response
from playgrounds.models import SportVenue
from playgrounds.serializers import SportVenueSerializer
from accounts.models import Role


class AdminSportVenueViewSet(viewsets.ModelViewSet):
    """
    ViewSet для владельцев полей и супер-админов.
    Доступ строго по JWT-токену.
    """

    serializer_class = SportVenueSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        # --- Если Swagger вызывает view — вернуть пустой QuerySet, чтобы не падало ---
        if getattr(self, "swagger_fake_view", False):
            return SportVenue.objects.none()

        user = self.request.user

        # --- Если пользователь не авторизован ---
        if not user.is_authenticated:
            # JWT не предоставлен — блокируем
            return SportVenue.objects.none()

        # --- Проверка ролей ---
        if user.is_superuser or user.role == Role.SUPERADMIN:
            return SportVenue.objects.all()
        elif user.role == Role.OWNER:
            return SportVenue.objects.filter(owner=user)
        else:
            # Любой другой (например, admin, staff, user) не имеет доступа
            return SportVenue.objects.none()

    @swagger_auto_schema(
        operation_summary="Получить список своих полей",
        operation_description="Возвращает список площадок, принадлежащих владельцу или всем площадкам для супер-админа. Требует авторизации.",
    )
    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Авторизация обязательна."}, status=status.HTTP_401_UNAUTHORIZED)
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новое поле",
        operation_description="Создаёт новое поле, автоматически привязанное к владельцу. Требует авторизации.",
    )
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Авторизация обязательна."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Просмотр конкретного поля",
        operation_description="Возвращает подробную информацию о поле. Только для авторизованных пользователей.",
    )
    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Авторизация обязательна."}, status=status.HTTP_401_UNAUTHORIZED)
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Редактировать поле",
        operation_description="Обновляет информацию о поле. Доступно только владельцу или супер-админу. Требует авторизации.",
    )
    def update(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Авторизация обязательна."}, status=status.HTTP_401_UNAUTHORIZED)
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить поле",
        operation_description="Удаляет поле, если оно принадлежит владельцу или если пользователь — супер-админ. Требует авторизации.",
    )
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Авторизация обязательна."}, status=status.HTTP_401_UNAUTHORIZED)
        return super().destroy(request, *args, **kwargs)
