# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import EventViewSet, telegram_webhook, BookingViewSet

# router = DefaultRouter()
# router.register(r"events", EventViewSet, basename="events")
# router.register(r'bookings', BookingViewSet, basename='booking')


# urlpatterns = [
#     path("", include(router.urls)),
#     path("webhooks/telegram/", telegram_webhook, name="bookings_telegram_webhook"),
# ]

from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, TransactionViewSet, telegram_webhook

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
# router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = router.urls

urlpatterns += [
    path("webhooks/telegram/", telegram_webhook, name="telegram_webhook"),
]