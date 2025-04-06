from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SportFieldViewSet

router = DefaultRouter()
router.register(r'fields', SportFieldViewSet, basename='sportfield')

urlpatterns = [
    path('', include(router.urls)),
]
