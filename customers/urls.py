from rest_framework.routers import DefaultRouter
from .views import OwnerVenueViewSet, OwnerEventViewSet, OwnerPaymentViewSet, OwnerStatisticsView

router = DefaultRouter()
router.register(r'owner/venues', OwnerVenueViewSet, basename='owner-venues')
router.register(r'owner/events', OwnerEventViewSet, basename='owner-events')
router.register(r'owner/payments', OwnerPaymentViewSet, basename='owner-payments')

urlpatterns = [
    *router.urls,
    path('owner/statistics/', OwnerStatisticsView.as_view(), name='owner-statistics'),
]
