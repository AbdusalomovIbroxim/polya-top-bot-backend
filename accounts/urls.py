from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TelegramAuthView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/telegram/', TelegramAuthView.as_view(), name='telegram-auth'),
]
