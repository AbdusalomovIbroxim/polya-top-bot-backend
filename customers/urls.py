from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    OwnerVenueViewSet,
    OwnerBookingViewSet,
    OwnerTransactionViewSet,
    OwnerStatisticsView,
)

router = DefaultRouter()
router.register(r'owner/venues', OwnerVenueViewSet, basename='owner-venues')
router.register(r'owner/bookings', OwnerBookingViewSet, basename='owner-bookings')
router.register(r'owner/transactions', OwnerTransactionViewSet, basename='owner-transactions')


urlpatterns = [
    *router.urls,
    path('owner/statistics/', OwnerStatisticsView.as_view(), name='owner-statistics'),
]
