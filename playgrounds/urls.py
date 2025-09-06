from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientSportVenueViewSet, FavoriteSportVenueViewSet, SportVenueTypeViewSet, RegionViewSet, send_contact

router = DefaultRouter()
router.register(r'types', SportVenueTypeViewSet)
router.register(r'sport-venues', ClientSportVenueViewSet)
router.register(r'favorites', FavoriteSportVenueViewSet, basename='favorite')
router.register(r'regions', RegionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('send-contant/', send_contact, name="send-contact"),
]
