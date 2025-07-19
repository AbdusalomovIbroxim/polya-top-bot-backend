from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SportVenueViewSet, FavoriteSportVenueViewSet, SportVenueTypeViewSet, RegionViewSet

router = DefaultRouter()
router.register(r'types', SportVenueTypeViewSet)
router.register(r'sport-venues', SportVenueViewSet)
router.register(r'favorites', FavoriteSportVenueViewSet, basename='favorite')
router.register(r'regions', RegionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 