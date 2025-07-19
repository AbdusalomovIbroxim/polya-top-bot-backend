from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SportVenueViewSet, FavoriteSportVenueViewSet, SportVenueTypeViewSet

router = DefaultRouter()
router.register(r'types', SportVenueTypeViewSet)
router.register(r'sport-venues', SportVenueViewSet)
router.register(r'favorites', FavoriteSportVenueViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
] 