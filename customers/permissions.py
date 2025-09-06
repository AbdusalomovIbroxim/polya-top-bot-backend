from rest_framework import permissions

class IsOwnerOfVenue(permissions.BasePermission):
    """Доступ только владельцу спортплощадки."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
