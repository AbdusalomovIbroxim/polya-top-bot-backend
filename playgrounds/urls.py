from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaygroundViewSet, FavoritePlaygroundViewSet

router = DefaultRouter()
router.register(r'playgrounds', PlaygroundViewSet, basename='playground')
router.register(r'favorites', FavoritePlaygroundViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
] 