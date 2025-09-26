from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrSuperAdmin(BasePermission):
    """
    Доступ разрешён только владельцам полей и супер-админам.
    """

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or getattr(user, "is_owner", False))

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_superuser:
            return True
        # проверка, что объект связан с владельцем
        if hasattr(obj, "owner"):
            return obj.owner == user
        if hasattr(obj, "stadium") and hasattr(obj.stadium, "owner"):
            return obj.stadium.owner == user
        return False
