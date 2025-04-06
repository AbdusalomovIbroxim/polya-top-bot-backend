from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
import os
import json
import hmac
import hashlib
import urllib.parse
from .models import Booking
from .serializers import UserSerializer, BookingSerializer
from .permissions import IsSuperAdmin

User = get_user_model()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


class TelegramWebAppAuthView(APIView):
    def post(self, request):
        init_data = request.data.get("initData")
        data = self.parse_init_data(init_data)

        if not self.check_signature(data, TELEGRAM_BOT_TOKEN):
            return Response({"detail": "Invalid signature"}, status=400)

        telegram_id = data["user"]["id"]
        first_name = data["user"].get("first_name")
        last_name = data["user"].get("last_name")
        username = data["user"].get("username")
        photo_url = data["user"].get("photo_url")

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={"first_name": first_name, "last_name": last_name, "username": username}
        )

        return Response({
            "username": user.username,
            "first_name": user.first_name,
            "photo_url": photo_url
        })

    def parse_init_data(self, init_data):
        parsed = dict(urllib.parse.parse_qsl(init_data))
        if "user" in parsed:
            parsed["user"] = json.loads(parsed["user"])
        return parsed

    def check_signature(self, data, token):
        check_hash = data.pop("hash", "")
        data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
        secret_key = hashlib.sha256(token.encode()).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return check_hash == calculated_hash


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list': # noqa
            if not self.request.user.is_superuser:
                return User.objects.filter(id=self.request.user.id)
        elif self.action == 'retrieve': # noqa
            if not self.request.user.is_superuser and self.request.user.id != self.kwargs['pk']:
                return User.objects.none()
        return super().get_queryset()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise permissions.PermissionDenied("You do not have permission to create a user.") # noqa
        super().perform_create(serializer)

    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.id != kwargs['pk']:
            return Response({"detail": "You do not have permission to view this user."}, status=403)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.id != kwargs['pk']:
            return Response({"detail": "You do not have permission to update this user."}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_superuser and request.user.id != kwargs['pk']:
            return Response({"detail": "You do not have permission to update this user."}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"detail": "You do not have permission to delete this user."}, status=403)
        return super().destroy(request, *args, **kwargs)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
