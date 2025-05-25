from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlaygroundViewSet,
    FavoritePlaygroundViewSet,
    PlaygroundTypeViewSet
)

router = DefaultRouter()
router.register(r'types', PlaygroundTypeViewSet)
router.register(r'playgrounds', PlaygroundViewSet)
router.register(r'favorites', FavoritePlaygroundViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
] 