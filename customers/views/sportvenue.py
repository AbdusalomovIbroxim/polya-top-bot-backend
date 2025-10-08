from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from playgrounds.models import SportVenue
from playgrounds.serializers import SportVenueSerializer
from ..permissions import IsOwnerOrSuperAdmin


class AdminSportVenueViewSet(viewsets.ModelViewSet):
    """
    ViewSet для владельцев полей и супер-админов.
    Позволяет управлять своими полями:
    - Просмотр списка своих полей
    - Просмотр подробной информации
    - Создание, редактирование и удаление
    """

    queryset = SportVenue.objects.all()
    serializer_class = SportVenueSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SportVenue.objects.all()
        return SportVenue.objects.filter(owner=user)

    @swagger_auto_schema(
        operation_summary="Получить список своих полей",
        operation_description="Возвращает список площадок, принадлежащих владельцу или всем площадкам для супер-админа.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новое поле",
        operation_description="Создаёт новое поле, привязанное к владельцу.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Просмотр конкретного поля",
        operation_description="Возвращает подробную информацию о выбранном поле.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Редактировать поле",
        operation_description="Обновляет информацию о поле. Доступно только владельцу или супер-админу.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить поле",
        operation_description="Удаляет поле, если оно принадлежит владельцу или если пользователь — супер-админ.",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
