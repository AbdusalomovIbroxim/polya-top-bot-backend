from rest_framework import permissions
from django.conf import settings
from djangoProject.utils import check_webapp_signature, parse_telegram_init_data
from accounts.models import User

class TelegramWebAppPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        init_data = request.data.get('init_data') or request.query_params.get('init_data')
        if not init_data:
            return False
        if not check_webapp_signature(settings.TELEGRAM_BOT_TOKEN, init_data):
            return False
        user_data = parse_telegram_init_data(init_data)
        if not user_data:
            return False
        telegram_id = user_data.get('id')
        if not telegram_id:
            return False
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return False
        request.user = user
        return True