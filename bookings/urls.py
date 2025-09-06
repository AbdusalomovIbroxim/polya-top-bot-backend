from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, telegram_webhook

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="events")

urlpatterns = [
    path("", include(router.urls)),
    path("webhooks/telegram/", telegram_webhook, name="bookings_telegram_webhook"),
]
