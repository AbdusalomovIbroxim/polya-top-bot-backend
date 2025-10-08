from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth import AdminAuthViewSet
from .views.dashboard import DashboardView
from .views.sportvenue import AdminSportVenueViewSet
from .views.user import UserManagementViewSet
from .views.bookings import BookingViewSet

router = DefaultRouter()
router.register(r'auth', AdminAuthViewSet, basename='admin-auth')
router.register(r'sportvenues', AdminSportVenueViewSet, basename='admin-sportvenues')
router.register(r'bookings', BookingViewSet, basename='booking-management')
router.register(r'users', UserManagementViewSet, basename='user-management')

urlpatterns = [
    path('admin-panel/', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
