from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import User, Role
from accounts.serializers import UserSerializer
from customers.permissions import IsSuperAdmin


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Управление пользователями (только супер админ).
    - Просмотр всех пользователей.
    - Фильтрация по ролям.
    - Создание, редактирование, удаление пользователей.
    - Назначение ролей.
    """
    queryset = User.objects.all().select_related('city')
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'city']
    search_fields = ['username', 'first_name', 'last_name', 'phone']
    ordering_fields = ['date_joined', 'username']

    def create(self, request, *args, **kwargs):
        """
        Создание нового пользователя (например, владельца поля).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = request.data.get('role', Role.CUSTOMER)

        # Устанавливаем роль
        user = serializer.save(role=role)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Редактирование данных пользователя.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление пользователя.
        """
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "Пользователь успешно удалён"}, status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """
        Логика создания (например, для владельцев можно сразу проставить дефолтные данные).
        """
        role = self.request.data.get('role', Role.CUSTOMER)
        serializer.save(role=role)
