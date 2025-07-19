from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, TelegramAuthViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'', TelegramAuthViewSet, basename='telegram-auth')

urlpatterns = [
    path('', include(router.urls)),
] 