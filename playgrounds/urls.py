from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientSportVenueViewSet, FavoriteSportVenueViewSet, SportVenueTypeViewSet, RegionViewSet, ContactFormAPIView

router = DefaultRouter()
router.register(r'types', SportVenueTypeViewSet)
router.register(r'sport-venues', ClientSportVenueViewSet)
router.register(r'favorites', FavoriteSportVenueViewSet, basename='favorite')
router.register(r'regions', RegionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('send-contact/', ContactFormAPIView.as_view(), name='send-contact'),
]
