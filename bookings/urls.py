from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, telegram_webhook

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/telegram/', telegram_webhook, name='telegram_webhook'),
] 